#include "hex-string.h"
#include <string.h>

namespace {
int HexDigit(unsigned char ch)
{
	if (ch >= '0' && ch <= '9')
		return ch - '0';
	if (ch >= 'a' && ch <= 'f')
		return ch - 'a' + 10;
	if (ch >= 'A' && ch <= 'F')
		return ch - 'A' + 10;
	return -1;
}
}

size_t UTIL_DecodeHexString(unsigned char *buffer, size_t maxlength, const char *hexstr)
{
	const size_t length = strlen(hexstr);
	size_t written = 0;
	for (size_t i = 0; i < length && written < maxlength; i++)
	{
		if (hexstr[i] == '\\' && length - i >= 4 && hexstr[i + 1] == 'x')
		{
			const int high = HexDigit(static_cast<unsigned char>(hexstr[i + 2]));
			const int low = HexDigit(static_cast<unsigned char>(hexstr[i + 3]));
			if (high >= 0 && low >= 0)
			{
				buffer[written++] = static_cast<unsigned char>((high << 4) | low);
				i += 3;
				continue;
			}
		}
		buffer[written++] = static_cast<unsigned char>(hexstr[i]);
	}
	return written;
}
