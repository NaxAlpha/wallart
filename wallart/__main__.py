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

import click

import wallart.highlight
import wallart.window


@click.command()
@click.argument("input", type=click.File("r"))
@click.argument("output", type=click.File("wb"))
@click.option("--ansi", help="Whether or not to process this as ANSI terminal output", default=False, type=bool)
@click.option("--style", help="Which Pygments style to use.", default="witchhazel")
@click.option("--term-theme", help="Which terminal theme to use, should be a path to an itermcolors file.", default=None)
def main(input, output, ansi: bool, style: str, term_theme: str):
    # Read the code file.
    code = input.read()

    # Use Pygments to create an image of the code file.
    code_image = wallart.highlight.highlight(code, ansi=ansi, style=style, term_theme=term_theme)

    # Draw the pretty window frame.
    final_image = wallart.window.draw_window(code_image, style=style)

    final_image.save(output)


# Allows using python3 -m wallart
if __name__ == '__main__':
    main()
