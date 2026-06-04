import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".claude", "skills", "dataparser", "scripts"))

from dataparser.tokenizer import parse_token, tokens_to_str, iter_batches


def test_parse_number():
    assert parse_token("42") == 42

def test_parse_ref():
    assert parse_token("$7") == "$7"

def test_tokens_to_str():
    assert tokens_to_str([1, 2, "$3"]) == "1 2 $3"

def test_iter_batches_even():
    tokens = list(range(10))
    batches = list(iter_batches(tokens, 5))
    assert len(batches) == 2
    assert batches[0] == (0, [0,1,2,3,4])
    assert batches[1] == (5, [5,6,7,8,9])

def test_iter_batches_uneven():
    tokens = list(range(7))
    batches = list(iter_batches(tokens, 3))
    assert len(batches) == 3
    assert batches[2] == (6, [6])
