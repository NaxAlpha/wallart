# Copyright 2019 Alethea Katherine Flowers
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re

import pygments.lexer
from PIL import Image, ImageDraw

from wallart import iterm


escape_re = re.compile(r"\[(?P<arg1>\d+)(;(?P<arg2>\d+)(;(?P<arg3>\d+))?)?m")


def int_or_none(val):
    try:
        return int(val)
    except TypeError:
        return None


class ConsoleOutputLexer(pygments.lexer.Lexer):
    def __init__(self, *args, theme: iterm.ITermColors = None, **kwargs):
        self.theme = theme
        super().__init__(*args, **kwargs)

    def get_tokens_unprocessed(self, text: str):
        pos = 0
        fg_color = self.theme.foreground_color
        bg_color = None
        decoration = None

        for match in escape_re.finditer(text):
            # Yield the current text with whatever the current color is.
            section = text[pos:match.start() - 1]
            yield (pos, (fg_color, bg_color, decoration), section)

            # Update the color.
            args = (
                match.group("arg1"),
                match.group("arg2"),
                match.group("arg3")
            )

            # Three arg form
            if args[1] and args[2]:
                style_arg = int_or_none(args[0])
                fg_arg = int_or_none(args[1])
                bg_arg = int_or_none(args[2])
            # One or two arg form.
            else:
                style_arg = int_or_none(args[0])
                fg_arg = int_or_none(args[0])
                bg_arg = int_or_none(args[1])

            if(style_arg == 0):
                fg_color = self.theme.foreground_color
                bg_color = None
                decoration = None

            if(style_arg == 1):
                decoration = "bold"

            if(style_arg == 2):
                # Semi transparent?
                decoration = "faint"

            if(style_arg == 3):
                # Semi transparent?
                decoration = "italic"

            if(style_arg == 4):
                # Semi transparent?
                decoration = "underline"

            if(fg_arg and fg_arg > 30):
                fg_color = self.theme.escape_code_to_color(fg_arg)

            if(bg_arg and bg_arg > 30):
                bg_color = self.theme.escape_code_to_color(bg_arg)

            pos = match.end()

        yield (pos, (fg_color, bg_color, decoration), text[pos:])


class ConsoleImageFormatter(pygments.formatters.ImageFormatter):
    """Modified from pygments.

    _create_drawables replaces with ttype with just the color/decoration tuple.
    format deals with drawing background colors where needed.
    """

    def _create_drawables(self, tokensource):
        lineno = charno = maxcharno = 0
        for ttype, value in tokensource:
            fg_color, bg_color, decoration = ttype
            # TODO: make sure tab expansion happens earlier in the chain.  It
            # really ought to be done on the input, as to do it right here is
            # quite complex.
            value = value.expandtabs(4)
            lines = value.splitlines(True)
            # print lines
            for i, line in enumerate(lines):
                temp = line.rstrip('\n')
                if temp:
                    self._draw_text(
                        self._get_text_pos(charno, lineno),
                        temp,
                        font=self._get_style_font({
                            "bold": decoration == "bold",
                            "italic": decoration == "italic",
                            "underline": decoration == "underline"
                        }),
                        fill=fg_color,
                        bg=bg_color
                    )
                    charno += len(temp)
                    maxcharno = max(maxcharno, charno)
                if line.endswith('\n'):
                    # add a line for each extra line in the value
                    charno = 0
                    lineno += 1
        self.maxcharno = maxcharno
        self.maxlineno = lineno

    def format(self, tokensource, outfile):
        """
        Format ``tokensource``, an iterable of ``(tokentype, tokenstring)``
        tuples and write it into ``outfile``.

        This implementation calculates where it should draw each token on the
        pixmap, then calculates the required pixmap size and draws the items.
        """
        self._create_drawables(tokensource)
        self._draw_line_numbers()
        im = Image.new(
            'RGB',
            self._get_image_size(self.maxcharno, self.maxlineno),
            self.background_color
        )
        self._paint_line_number_bg(im)
        draw = ImageDraw.Draw(im)

        # Highlight
        if self.hl_lines:
            x = (
                self.image_pad + self.line_number_width
                - self.line_number_pad + 1)
            recth = self._get_line_height()
            rectw = im.size[0] - x
            for linenumber in self.hl_lines:
                y = self._get_line_y(linenumber - 1)
                draw.rectangle([(x, y), (x + rectw, y + recth)],
                               fill=self.hl_color)

        for pos, value, font, kw in self.drawables:
            bg = kw.pop("bg", None)
            if bg:
                draw.rectangle(
                    [
                        pos[0],
                        pos[1],
                        pos[0] + self.fontw * len(value),
                        pos[1] + self._get_line_height()
                    ],
                    fill=bg)
            draw.text(pos, value, font=font, **kw)

        im.save(outfile, self.image_format.upper())
