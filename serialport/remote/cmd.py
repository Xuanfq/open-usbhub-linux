import logging
import asyncio
import inspect
from cmd import Cmd
from usbhub import USBHUBDevice

CR, LF, NUL, SPACE = "\r\n\x00\x20"


class AsyncStream:
    def __init__(self, reader, writer):
        self.reader = reader
        self.writer = writer

    async def readline(self):
        data = await self.reader.readuntil(b"\n")
        return data.decode().strip() + "\n"

    async def read(self, n: int = -1):
        data = await self.reader.read(n)
        return data

    def write(self, data: str | bytes, str_char_enter_fixed: bool = True):
        if isinstance(data, str):
            if str_char_enter_fixed:
                self.writer.write(
                    str(data).replace("\r\n", "\n").replace("\n", "\r\n").encode()
                )
            else:
                self.writer.write(str(data).encode())
        else:
            self.writer.write(data)
        asyncio.create_task(self.writer.drain())

    def writeline(self, data: str | bytes):
        if isinstance(data, str):
            data = f"{data}\r\n"
        else:
            data = data + b"\r\n"
        self.write(data)

    def writelines(self, data: str | bytes):
        self.writeline(data)

    async def drain(self):
        await self.writer.drain()

    def flush(self):
        pass


class AsyncRemoteCmd(Cmd):
    use_rawinput = 0
    prompt = "(shell) "
    intro = None

    def do_exit(self, arg):
        """Exit the shell."""
        self.stdout.write("\r\nBye!\r\n\r\n")
        return True

    def default(self, line):
        self.stdout.write(
            f"\r\nUnknown command '{line}'. Type help or ? to list commands.\r\n\r\n"
        )

    def emptyline(self):
        pass

    async def onecmd(self, line):
        """Interpret the argument as though it had been typed in response
        to the prompt.

        This may be overridden, but should not normally need to be;
        see the precmd() and postcmd() methods for useful execution hooks.
        The return value is a flag indicating whether interpretation of
        commands by the interpreter should stop.

        """
        cmd, arg, line = self.parseline(line)
        if not line:
            return self.emptyline()
        if cmd is None:
            return self.default(line)
        self.lastcmd = line
        if line == "EOF":
            self.lastcmd = ""
        if cmd == "":
            return self.default(line)
        else:
            try:
                func = getattr(self, "do_" + cmd)
            except AttributeError:
                return self.default(line)
            if inspect.iscoroutinefunction(func):
                return await func(arg)
            else:
                return func(arg)

    def complete(self, text, state, remote: bool = False):
        """Return the next possible completion for 'text'.

        If a command has not been entered, then complete against command list.
        Otherwise try to call complete_<command> to get list of completions.
        """
        is_compfunc_type_name = False
        if state == 0:
            if not remote:
                import readline

                origline = readline.get_line_buffer()
                line = origline.lstrip()
                stripped = len(origline) - len(line)
                begidx = readline.get_begidx() - stripped
                endidx = readline.get_endidx() - stripped
            else:
                origline = text
                line = origline.lstrip()
                stripped = len(origline) - len(line)
                begidx = len(origline) - stripped
                endidx = len(origline) - stripped
            if begidx > 0:
                cmd, args, foo = self.parseline(line)
                if cmd == "":
                    compfunc = self.completedefault
                else:
                    try:
                        compfunc = getattr(self, "complete_" + cmd)
                    except AttributeError:
                        is_compfunc_type_name = True
                        compfunc = self.completenames
            else:
                is_compfunc_type_name = True
                compfunc = self.completenames
            self.completion_matches = compfunc(text, line, begidx, endidx)
        try:
            if (
                is_compfunc_type_name
                and isinstance(self.completion_matches, list)
                and len(self.completion_matches) == 1
            ):
                return self.completion_matches[0]
            return self.completion_matches
        except IndexError:
            return None

    def completenames(self, text, *ignored):
        dotext = "do_" + text
        matches = [a[3:] for a in self.get_names() if a.startswith(dotext)]
        if len(matches) == 1:
            return matches[0] + " "
        return matches

    def completetips(
        self,
        text,
        line,
        begidx,
        endidx,
        tips: list[str] | dict[str, list[str]] | dict[str, dict],
    ):
        if len(tips) == 0:
            return None
        cmd, args, foo = self.parseline(line)
        args_list = args.split()
        args_size = len(args_list)
        matches, futures = [], []
        if not args:
            futures = list(tips.keys()) if isinstance(tips, dict) else tips
        else:
            dtips = tips.copy()
            deep = 0
            while deep < args_size:
                if not (
                    isinstance(dtips, str)
                    or isinstance(dtips, list)
                    or isinstance(dtips, dict)
                    or isinstance(dtips, int)
                    or isinstance(dtips, float)
                ):
                    # matches = []
                    # futures = []
                    break
                if (
                    isinstance(dtips, str)
                    # and args_list[deep] == dtips
                    or isinstance(dtips, int)
                    # and int(args_list[deep]) == dtips
                    or isinstance(dtips, float)
                    # and float(args_list[deep]) == dtips
                ):
                    # str
                    if str(args_list[deep]) == str(dtips):
                        matches.append(dtips)
                    elif str(dtips).startswith(str(args_list[deep])):
                        futures = dtips
                    # if deep + 1 != args_size:
                    #     matches = []
                    break
                elif args_list[deep] in dtips:
                    # dict or list
                    matches.append(args_list[deep])
                    if isinstance(dtips, dict):
                        dtips = dtips[args_list[deep]]
                    elif isinstance(dtips, list):
                        dtips = dtips[dtips.index(args_list[deep])]
                    futures = dtips
                    if isinstance(futures, dict):
                        futures = list(futures.keys())
                    elif not isinstance(futures, list):
                        futures = []
                else:
                    if isinstance(dtips, dict):
                        futures = list(dtips.keys())
                    elif isinstance(dtips, list):
                        futures = dtips
                    break
                deep += 1
        logging.debug(f"completetips: {matches}, {futures}, {args_list}, {args_size}")
        if len(matches) + 1 >= args_size or args_size == 0:
            if len(futures) == 0:
                return None
            last_arg = args_list[-1] if args_size > len(matches) else None
            future_matches = (
                [str(s) for s in futures if str(s).startswith(last_arg)]
                if last_arg
                else [str(s) for s in futures]
            )
            logging.debug(f"completetips future_matches: {future_matches}")
            if future_matches:
                prefix = future_matches[0]
                prefix_complete = True
                for s in future_matches[1:]:
                    prefix_complete = False
                    while s[: len(prefix)] != prefix and prefix:
                        prefix = prefix[:-1]
                        if not prefix:
                            break
                logging.debug(f"completetips prefix: {prefix}")
                if prefix and (
                    len(future_matches) == 1 or not last_arg or prefix != last_arg
                ):
                    tipcmd = cmd + " "
                    if matches:
                        tipcmd += " ".join(matches) + " "
                    tipcmd += prefix
                    if prefix_complete:
                        tipcmd += " "
                    return tipcmd
                return future_matches
            return None
        else:
            return None

    def complete_help(self, *args):
        topics = list(set(a[3:] for a in self.get_names() if a.startswith("do_")))
        return self.completetips(*args, tips=topics)

    async def cmdloop(self, intro=None, use_remote_rawinput: bool = True):
        use_rawinput = not use_remote_rawinput
        error_exit = False
        self.preloop()
        if use_rawinput and self.completekey:
            try:
                import readline

                self.old_completer = readline.get_completer()
                readline.set_completer(self.complete)
                readline.parse_and_bind(self.completekey + ": complete")
            except ImportError:
                pass
        elif use_remote_rawinput and self.completekey:
            # Negotiate_character_mode，track single character input
            # IAC WILL ECHO
            self.stdout.write(b"\xFF\xFB\x01")
            # IAC WILL SGA (Suppress Go Ahead)
            self.stdout.write(b"\xFF\xFB\x03")
            await self.stdout.drain()
            await self.stdin.read(6)  # read buffer
            pass
        try:
            if intro is not None:
                self.intro = intro
            if self.intro:
                self.stdout.write(str(self.intro) + "\n")
            stop = None
            linebuffer = b""
            linecur = 0
            newline = True
            while not stop:
                line = ""
                if self.cmdqueue:
                    line = self.cmdqueue.pop(0)
                elif use_rawinput:
                    try:
                        line = input(self.prompt)
                    except EOFError:
                        line = "EOF"
                elif use_remote_rawinput:
                    if newline:
                        self.stdout.write(self.prompt)
                        newline = False

                    char = await self.stdin.read(1)
                    # logging.debug(f"recv:{char}")

                    while char in [
                        b"\xff",
                        b"\xfb",
                        b"\xfc",
                        b"\xfd",
                        b"\xfe",
                        b"\x00",
                        b"\x48",  # up
                        b"\x50",  # down
                        b"\x1b",  # up/down
                    ]:
                        # Handle IAC sequences (Interpret As Command)
                        char = await self.stdin.read(1)

                    if not char:
                        line = "EOF"

                    if char == "\x4b":  # left
                        cur = cur - 1 if cur > 0 else 0
                    elif char == "\x4d":  # right
                        cur = cur if cur == len(linebuffer) else cur + 1

                    elif char == b"\r":  # Carriage return
                        self.stdout.writeline("")
                        line = linebuffer.decode().strip()
                        linebuffer = b""
                        linecur = 0
                        newline = True
                    elif char == b"\x7f":  # Backspace/Delete
                        if linebuffer:
                            linebuffer = linebuffer[:-1]
                            self.stdout.write(
                                f"\r{SPACE*(len(self.prompt)+len(linebuffer)+1)}".encode()
                            )
                            self.stdout.write(f"\r{self.prompt}".encode() + linebuffer)
                    elif char == b"\t":  # Tab completion
                        matches = self.complete(linebuffer.decode(), 0, True)
                        if matches:
                            logging.debug(f"matches: {matches}")
                            if isinstance(matches, list):
                                self.stdout.writelines(
                                    f"\r\n{' '.join(matches)}".encode()
                                )
                            else:
                                self.stdout.write(
                                    f"\r{SPACE*(len(self.prompt)+len(linebuffer))}".encode()
                                )
                                linebuffer = matches.encode()
                            self.stdout.write(f"\r{self.prompt}".encode() + linebuffer)
                    else:
                        linebuffer += char
                        self.stdout.write(
                            f"\r{SPACE*(len(self.prompt)+len(linebuffer))}".encode()
                        )
                        self.stdout.write(f"\r{self.prompt}".encode() + linebuffer)
                else:
                    self.stdout.write(self.prompt)
                    self.stdout.flush()
                    # line = self.stdin.readline()
                    line = await self.stdin.readline()
                    if not len(line):
                        line = "EOF"
                    else:
                        line = line.rstrip("\r\n")
                if line:
                    logging.debug(f"line:{line},{self.parseline(line)}")
                    line = self.precmd(line)
                    stop = await self.onecmd(line)
                    stop = self.postcmd(stop, line)
            self.postloop()
        except Exception as e:
            error_exit = True
        finally:
            if use_rawinput and self.completekey:
                try:
                    import readline

                    readline.set_completer(self.old_completer)
                except ImportError:
                    pass
            return error_exit
