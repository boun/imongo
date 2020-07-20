import json
import os
import re
import signal
import dateutil.parser
import uuid
from subprocess import check_output

from metakernel import ProcessMetaKernel as Kernel
from pexpect import replwrap, EOF

from . import utils

__version__ = '0.3.0'
version_pat = re.compile(r'version\D*(\d+(\.\d+)+)')

log_file = os.path.join(os.path.split(__file__)[0], 'imongo_kernel.log')
logger = utils.make_logger('IMongo', fname=log_file)
logger.info(f'Logging to {log_file}')


class MongoShellWrapper(replwrap.REPLWrapper):
    child = {}
    """
    A subclass of REPLWrapper specific for the MongoDB shell.
    run_command is the only method overridden.
    """

    def __init__(self, *args, **kwargs):
        replwrap.REPLWrapper.__init__(self, *args, **kwargs)
        logger.info('Constructor MongoShellWrapper')
        self.args = args
        self.kwargs = kwargs

    @staticmethod
    def _filter_response(res):
        msg = re.sub('\[\d+[A-Z]', '', res)
        msg = re.sub('\[J', '', msg)
        msg = [l.strip() for l in msg.split('\x1b') if l]

        output = []
        for l in msg[::-1]:
            if not output:
                output.append(l)
                continue
            if l not in output[-1]:
                output.append(l)
        return output[0]

    def _isbufferempty(self):
        condition1 = self.child.buffer.strip() == '\x1b[47G\x1b[J\x1b[47G'
        condition2 = self.child.buffer.strip() == ''
        return condition1 or condition2

    def _send_line(self, cmd):
        try:
            self.child.sendline(cmd)
            logger.debug('Command sent. Waiting for prompt')
        except Exception as e:
            exception_msg = 'Unexpected exception occurred.'
            logger.error('{}: {}: {}'.format(
                exception_msg, e.__class__.__name__, e.args))
            raise RuntimeError(exception_msg)

    def _expect_prompt(self, timeout=5):
        return self.child.expect([self.prompt, self.continuation_prompt],
                                 timeout=timeout)

    def run_command(self, command, timeout=-1, **kwargs):
        logger.info('COMMAND ' + command[:200])
        """Send a command to the REPL, wait for and return output.

        :param str command: The command to send. Trailing newlines are not needed.
          This should be a complete block of input that will trigger execution;
          if a continuation prompt is found after sending input, :exc:`ValueError`
          will be raised.
        :param int timeout: How long to wait for the next prompt. -1 means the
          default from the :class:`pexpect.spawn` object (default 30 seconds).
          None means to wait indefinitely.
        """
        # Clean input command by removing indentation and comment lines
        # There seems to be a limitation with pexepect/mongo when entering
        # lines longer than 1000 characters. If that is the case, a ValueError
        # exception is raised.
        cmd_lines = [l for l in command.splitlines() if l and not l.startswith('//')]
        cmd = re.sub('\s{2,}', ' ', ' '.join(cmd_lines))
        if len(cmd) > 1024:
            # TODO: Enable sending lines long lines (>1024 on macOS >4096 on Linux).
            # This is related to a buffering issue and seems that can only be solved
            # by splitting lines, and waiting for the continuation prompt.
            # However this MAY interfere with how responses are currently received
            # Ref:
            # http://pexpect.readthedocs.io/en/stable/_modules/pexpect/pty_spawn.html#spawn.send
            error = ('Code too long. Please commands with less than 1024 effective chracters.\n'
                     'Indentation spaces/tabs don\'t count towards "effective" characters.')
            logger.error(error)
            raise ValueError(error.replace('\n', ' '))

        self._send_line(cmd)
        matched_index = self._expect_prompt(timeout=timeout)

        response = []
        while not self._isbufferempty():
            response.append(self.child.before)
            logger.debug('Buffer not empty, sending blank line')
            matched_index = self._expect_prompt(timeout=timeout)
            if matched_index == 1:
                # If continuation prompt is detected (by the match in
                # _expect_prompt), restart child (by raising ValueError)
                error = ('Code incomplete. Please enter valid and complete code.\n'
                         'Continuation prompt functionality not implemented yet.')
                logger.error(error.replace('\n', ' '))
                raise ValueError(error)
            self._send_line('')
        response.append(self.child.before)
        response = self._filter_response(''.join(response))

        logger.debug('Response: {}'.format(response))

        return response


class MongoKernel(Kernel):
    implementation = 'IMongo'
    implementation_version = __version__
    _banner = None
    language_info = {'name': 'javascript',
                     'codemirror_mode': 'shell',
                     'mimetype': 'text/x-mongodb',
                     'file_extension': '.js'}

    @property
    def language_version(self):
        m = version_pat.search(self.banner)
        return m.group(1)

    @property
    def banner(self):
        if self._banner is None:
            self._banner = check_output(
                ['mongo', '--version']).decode('utf-8').strip()
        return self._banner

    def __init__(self, **kwargs):
        super(MongoKernel, self).__init__(**kwargs)
        logger.debug(self.language_info)
        logger.debug(self.language_version)
        logger.debug(self.banner)
        self.connection = False

    def makeWrapper(self):
        """Spawns `mongo` subprocess"""

        prompt = 'mongo{}mongo'.format(uuid.uuid4())
        cont_prompt = '\.\.\. $'
        prompt_cmd = "prompt = '{}'".format(prompt)

        # dir_func is an assistant Javascript function to be used by do_complete.
        # May be a slightly hackish approach.
        # http://stackoverflow.com/questions/5523747/equivalent-of-pythons-dir-in-javascript
        nop_func = """function nop() { return "";}"""
        dir_func = """function dir(object) {
                          attributes = [];
                          for (attr in object) {attributes.push(attr);}
                          attributes.sort();
                          return attributes;}"""
        try:
            spawn_cmd = ['mongo', f'--eval "{prompt_cmd}; {dir_func}; {nop_func}"', '--shell']
            wrapper = MongoShellWrapper(' '.join(spawn_cmd), orig_prompt=prompt,
                                                  prompt_change=None, continuation_prompt=cont_prompt)
        finally:
            # Signal handlers are inherited by forked processes, and we can't easily
            # reset it from the subprocess. Since kernelapp ignores SIGINT except in
            # message handlers, we need to temporarily reset the SIGINT handler here
            # so that bash and its children are interruptible.
            sig = signal.signal(signal.SIGINT, signal.SIG_DFL)
            signal.signal(signal.SIGINT, sig)

        return wrapper

    @staticmethod
    def _parse_shell_output_to_json(shell_output):
        logger.debug("OUT: " + shell_output)
        json_loader = utils.exception_logger(json.loads)

        # TODO: Parse booleans, Binaries, etc
        try:
            return json.loads(shell_output)
        except json.JSONDecodeError:
            output = []
            for doc in [line for line in shell_output.splitlines() if line]:
                doc = re.sub('WriteResult\((.*?)\)', '{"$result": "\\1"}', doc)
                doc = re.sub('ISODate\(\"(.*?)\"\)', '{"$date": "\\1"}', doc)
                doc = re.sub('ObjectId\(\"(.*?)\"\)', '{"$oid": "\\1"}', doc)
                doc = re.sub('NumberLong\(\"(.*?)\"\)',
                             '{"$numberLong": "\\1"}', doc)
                doc = json_loader(doc)
                if doc:
                    output.append(doc)
            return output

    def do_execute_direct(self, code):

        # Defer connecting to mongo, otherwise the notebook blocks if mongo is
        # not running
        output = super(MongoKernel, self).do_execute_direct(code, True)
        output.output += self.wrapper.run_command("nop()")
        if self.kernel_resp["status"] != "ok":
            error_msg = {'name': 'stderr', 'text': self.kernel_resp}
            self.send_response(self.iopub_socket, 'stream', self.kernel_resp)

        if output:
            # BOUN Hier wird der String rein geworfen
            output = output.output
            json_data = self._parse_shell_output_to_json(output)
            plain_msg = output

            if json_data:
                display_content = {
                    'data': {
                        'application/json': json_data
                    }, 'metadata': {}
                }
                logger.debug("JSON Response")
                logger.debug(display_content)
                self.send_response(self.iopub_socket, 'display_data', display_content)
                return

            logger.debug("PLAIN Response -- Check for Error")
            logger.debug(plain_msg)
            try:
                ts = dateutil.parser.parse( plain_msg.split(" ")[0])
                self.send_response(self.iopub_socket, 'stream', {'name': 'stderr', 'text': (plain_msg)})
                logger.debug("ERROR Response")
                return
            except Exception as e:
                pass
            
            self.send_response(self.iopub_socket, 'stream', {'name': 'stdout', 'text': (plain_msg)})

        return

if __name__ == '__main__':
    MongoKernel.run_as_main()

