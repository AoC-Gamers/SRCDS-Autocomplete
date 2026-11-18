#include "hex-string.h"
#include <assert.h>
#include <string.h>
#include <vector>
#include <stdio.h>

static void Check(const char *input, const std::vector<unsigned char> &expected)
{
	// Every capacity, including zero and truncation inside each escape.
	for (size_t capacity = 0; capacity <= expected.size() + 1; capacity++)
	{
		std::vector<unsigned char> buffer(capacity + 2, 0xcd);
		const size_t written = UTIL_DecodeHexString(buffer.data() + 1, capacity, input);
		const size_t wanted = capacity < expected.size() ? capacity : expected.size();
		assert(written == wanted);
		assert(buffer.front() == 0xcd && buffer.back() == 0xcd);
		for (size_t i = 0; i < written; i++)
			assert(buffer[i + 1] == expected[i]);
		for (size_t i = written; i < capacity; i++)
			assert(buffer[i + 1] == 0xcd);
	}
}

int main()
{
	Check("", {});
	Check("\xff", {255});
	assert(UTIL_DecodeHexString(nullptr, 0, "\\x41") == 0);
	Check("plain", {'p', 'l', 'a', 'i', 'n'});
	Check("A\\x00\\xFfZ", {'A', 0, 255, 'Z'});
	for (const char *input : {"\\", "\\x", "\\xA", "\\xGG", "\\x1G", "\\x+1", "\\x 1"})
		Check(input, std::vector<unsigned char>(input, input + strlen(input)));
	Check("\\xGG\\x41", {'\\', 'x', 'G', 'G', 'A'});
	// Exhaust all byte values; %x must never accept a partial or signed pair.
	for (unsigned int value = 0; value <= 255; value++)
	{
		char escape[5];
		snprintf(escape, sizeof(escape), "\\x%02x", value);
		Check(escape, {static_cast<unsigned char>(value)});
	}
	puts("hex-string: all bytes, malformed input, capacities and canaries passed");
}
