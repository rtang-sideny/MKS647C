# Copyright (C) 2018, see AUTHORS.md
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from mks647c.syntax import OptionalSyntax, FixedLengthToken, IntegerToken, ConstantToken, FloatToken, ConcatSyntax, \
    OrSyntax, WhitespaceToken, UntilToken


class GrammarChannelMessage:
    KEY_OPT_WHITESPACE = 'Optional:whitespace'
    KEY_OPT_PARAMETER_2 = 'Optional:p2'
    KEY_OPT_PARAMETER_3 = 'Optional:p3'
    KEY_OPT_ADDITIONAL_TERMINATOR = 'Optional:nl'
    KEY_WHITESPACE = 'whitespace'
    KEY_COMMAND = 'Command'
    KEY_CHANNEL = 'Channel'
    KEY_QUERY = 'Query'
    KEY_WRITE = 'Write'
    KEY_QUERY_WRITE = 'Query/Write'
    KEY_PARAMETER_1 = 'Parameter1'
    KEY_PARAMETER_2 = 'Parameter2'
    KEY_PARAMETER_3 = 'Parameter3'
    KEY_TERMINATOR = 'CarriageReturn'
    KEY_ADDITIONAL_TERMINATOR = 'NewLine'

    KEY_SYNTAX = 'syntax'

    QUERY_TOKEN = 'R'

    def __init__(self):
        self._syntax = self._setup()

    def _setup(self):
        whitespace = OptionalSyntax(self.KEY_OPT_WHITESPACE, WhitespaceToken(self.KEY_WHITESPACE))
        cmd = FixedLengthToken(self.KEY_COMMAND, 2)
        channel = IntegerToken(self.KEY_CHANNEL)
        query = ConstantToken(self.KEY_QUERY, self.QUERY_TOKEN)
        p1 = FloatToken(self.KEY_PARAMETER_1)
        p2 = OptionalSyntax(self.KEY_OPT_PARAMETER_2, FloatToken(self.KEY_PARAMETER_2))
        p3 = OptionalSyntax(self.KEY_OPT_PARAMETER_3, FloatToken(self.KEY_PARAMETER_3))
        write = ConcatSyntax(self.KEY_WRITE, [p1, whitespace, p2, whitespace, p3])
        query_write = OrSyntax(self.KEY_QUERY_WRITE, [query, write])
        cr = ConstantToken(self.KEY_TERMINATOR, chr(0x0d))
        nl = OptionalSyntax(self.KEY_OPT_ADDITIONAL_TERMINATOR,
                            ConstantToken(self.KEY_ADDITIONAL_TERMINATOR, chr(0x0a)))

        return ConcatSyntax(self.KEY_SYNTAX, [cmd, whitespace, channel, whitespace, query_write, cr, nl])

    def get_syntax(self):
        return self._syntax

    def generate(self, data: 'DataChannelMessage'):
        return self._syntax.generate(**data.get_data())


class DataChannelMessage:
    def __init__(self):
        self._p1, self._p2, self._p3 = None, None, None
        self._cmd, self._channel, self._query_write = None, None, None

    def get_data(self):
        return {
            GrammarChannelMessage.KEY_CHANNEL: self._channel,
            GrammarChannelMessage.KEY_COMMAND: self._cmd,
            GrammarChannelMessage.KEY_QUERY_WRITE: self._query_write,
            GrammarChannelMessage.KEY_OPT_WHITESPACE: True,
            GrammarChannelMessage.KEY_OPT_ADDITIONAL_TERMINATOR: True,

            GrammarChannelMessage.KEY_PARAMETER_1: self._p1,

            GrammarChannelMessage.KEY_OPT_PARAMETER_2: self._p2 is None,
            GrammarChannelMessage.KEY_PARAMETER_2: self._p2,

            GrammarChannelMessage.KEY_OPT_PARAMETER_3: self._p3 is None,
            GrammarChannelMessage.KEY_PARAMETER_3: self._p3,
        }

    def set_command(self, command: str):
        if not len(command) == 2:
            raise ArgumentInvalidError("Command must have a length of two")

        self._cmd = command

    def set_channel(self, channel: int):
        if not (1 <= channel <= 8):
            raise ArgumentInvalidError("Channel must be between 1 and 8")

        self._channel = channel

    def set_query(self):
        self._query_write = {GrammarChannelMessage.KEY_QUERY: True}

    def set_write(self):
        self._query_write = {GrammarChannelMessage.KEY_WRITE: True}

    def set_parameter_1(self, param):
        self._p1 = param

    def set_parameter_2(self, param):
        self._p2 = param

    def set_parameter_3(self, param):
        self._p3 = param

    def get_command(self):
        return self._cmd

    def get_channel(self):
        return self._channel

    def get_parameter_1(self):
        return self._p1

    def get_parameter_2(self):
        return self._p2

    def get_parameter_3(self):
        return self._p3


class GrammarGeneralResponse:
    KEY_SYNTAX = 'syntax'
    KEY_VALUE = 'value'
    KEY_VALUE_1 = 'v1'
    KEY_VALUE_2 = 'v2'

    KEY_ERROR = 'error'
    KEY_ERROR_TOKEN = 'error_token'
    KEY_ERROR_CODE = 'ec'
    KEY_TERMINATOR = 'crnl'
    KEY_OPT_VALUE_2 = 'Optional:v2'
    KEY_VALUE_OR_ERROR = 'Or:v_e'
    KEY_OPT_WHITESPACE = 'Optional:whitespace'
    KEY_OPT_VALUE_ERROR = 'Optional:data'
    KEY_WHITESPACE = 'whitespace'

    def __init__(self):
        self._syntax = self._setup()

    def _value_1_token(self):
        raise NotImplementedError()

    def _value_2_token(self):
        return UntilToken(self.KEY_VALUE_2, chr(0x0d))

    def _setup(self):
        whitespace = OptionalSyntax(self.KEY_OPT_WHITESPACE, WhitespaceToken(self.KEY_WHITESPACE))
        error_token = ConstantToken(self.KEY_ERROR_TOKEN, 'E')
        error_code = IntegerToken(self.KEY_ERROR_CODE)
        error = ConcatSyntax(self.KEY_ERROR, [error_token, whitespace, error_code])
        v1 = self._value_1_token()
        v2 = OptionalSyntax(self.KEY_OPT_VALUE_2, self._value_2_token())
        value = ConcatSyntax(self.KEY_VALUE, [v1, v2])
        value_error = OrSyntax(self.KEY_VALUE_OR_ERROR, [value, error])
        terminal = ConstantToken(self.KEY_TERMINATOR, "" + chr(0x0d) + chr(0x0a))
        return ConcatSyntax(self.KEY_SYNTAX, [OptionalSyntax(self.KEY_OPT_VALUE_ERROR, value_error), terminal])


class DataGeneralResponse:
    def __init__(self, data):
        self._read(data)

    def _read(self, data):
        self._has_data = data[GrammarGeneralResponse.KEY_OPT_VALUE_ERROR]
        terminal = data[GrammarGeneralResponse.KEY_TERMINATOR]

        self._v1 = self._get(GrammarGeneralResponse.KEY_VALUE_1, data, None)
        self._v2 = self._get(GrammarGeneralResponse.KEY_VALUE_2, data, None,
                             exists=GrammarGeneralResponse.KEY_OPT_VALUE_2)

        self._has_error = self._get(GrammarGeneralResponse.KEY_ERROR_TOKEN, data, None) is not None
        self._error_code = self._get(GrammarGeneralResponse.KEY_ERROR_CODE, data, None)

        error_or_value = data[GrammarGeneralResponse.KEY_VALUE_OR_ERROR]

    def _get(self, key, data, default, exists=None):
        if exists is None:
            if key in data:
                return data[key]
            return default
        else:
            if exists in data and key in data:
                return data[key]
            return default

    def has_data(self):
        return self._has_data

    def has_error(self):
        return self._has_error

    def get_error_code(self):
        return self._error_code

    def get_value_1(self):
        return self._v1

    def get_value_2(self):
        return self._v2


class GrammarIntegerResponse(GrammarGeneralResponse):
    def _value_1_token(self):
        return IntegerToken(self.KEY_VALUE_1)
