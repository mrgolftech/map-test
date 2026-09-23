BIN_CHAR_ALPHABET = "123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"


def soft_bin_to_char(soft_bin: int) -> str | None:
    if soft_bin < 1 or soft_bin > len(BIN_CHAR_ALPHABET):
        return None
    return BIN_CHAR_ALPHABET[soft_bin - 1]


def char_to_soft_bin(source_char: str) -> int | None:
    if len(source_char) != 1:
        return None
    try:
        return BIN_CHAR_ALPHABET.index(source_char) + 1
    except ValueError:
        return None
