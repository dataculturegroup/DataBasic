"""
Tests for databasic.logic.wordhandler.

This module covers:
- basic word count behavior
- stop word handling
- case sensitivity
- n-gram toggles
- MAX_ITEMS truncation on large input
"""

# Standard library imports
import os
import unittest

# Local imports
import databasic.logic.filehandler as filehandler
import databasic.logic.wordhandler as wordhandler

class WordHandlerTest(unittest.TestCase):
    """
    Test cases for word counting helpers.
    """

    def setUp(self):
        """
        Set up the fixtures directory used by file-based tests.
        """
        self._fixtures_dir = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "fixtures",
        )

    def test_too_many_counts(self):
        """
        Counts should be truncated to MAX_ITEMS for large inputs.
        """
        fixture_path = os.path.join(self._fixtures_dir, "22kAmazonGameReview.txt")
        words = filehandler.convert_to_txt(fixture_path)
        counts = wordhandler.get_word_counts(words, True, True, "english")

        self.assertEqual(len(counts["unique_words"]), wordhandler.MAX_ITEMS)
        self.assertEqual(len(counts["bigrams"]), wordhandler.MAX_ITEMS)
        self.assertEqual(len(counts["trigrams"]), wordhandler.MAX_ITEMS)

    def test_get_word_counts_uses_default_text_when_text_is_none(self):
        """
        Passing None should analyze the module default text.
        """
        counts = wordhandler.get_word_counts(None)

        self.assertIn("unique_words", counts)
        self.assertIn("bigrams", counts)
        self.assertIn("trigrams", counts)
        self.assertIn("total_word_count", counts)
        self.assertGreater(counts["total_word_count"], 0)

    def test_can_disable_bigrams_and_trigrams(self):
        """
        Bigrams and trigrams should be empty when disabled.
        """
        counts = wordhandler.get_word_counts(
            "one two three",
            True,
            True,
            "english",
            get_bigrams=False,
            get_trigrams=False,
        )

        self.assertEqual(counts["bigrams"], [])
        self.assertEqual(counts["trigrams"], [])
        self.assertEqual(counts["total_word_count"], 3)

    def test_ignore_case_combines_words(self):
        """
        Words differing only by case should be merged when ignore_case is True.
        """
        counts = wordhandler.get_word_counts(
            "Sam sam SAM",
            ignore_case=True,
            ignore_stop_words=False,
            stopwords_language="english",
            get_bigrams=False,
            get_trigrams=False,
        )

        unique_words = dict(counts["unique_words"])
        self.assertEqual(unique_words["sam"], 3)
        self.assertEqual(len(unique_words), 1)

    def test_case_sensitive_counts_words_separately(self):
        """
        Words differing only by case should remain separate when ignore_case is False.
        """
        counts = wordhandler.get_word_counts(
            "Sam sam SAM",
            ignore_case=False,
            ignore_stop_words=False,
            stopwords_language="english",
            get_bigrams=False,
            get_trigrams=False,
        )

        unique_words = dict(counts["unique_words"])
        self.assertEqual(unique_words["Sam"], 1)
        self.assertEqual(unique_words["sam"], 1)
        self.assertEqual(unique_words["SAM"], 1)

    def test_ignore_stop_words_removes_common_words(self):
        """
        Common stop words should be removed when ignore_stop_words is True.
        """
        counts = wordhandler.get_word_counts(
            "the cat and the hat",
            ignore_case=True,
            ignore_stop_words=True,
            stopwords_language="english",
            get_bigrams=False,
            get_trigrams=False,
        )

        unique_words = dict(counts["unique_words"])
        self.assertNotIn("the", unique_words)
        self.assertNotIn("and", unique_words)
        self.assertIn("cat", unique_words)
        self.assertIn("hat", unique_words)

    def test_stop_words_can_be_kept(self):
        """
        Stop words should remain when ignore_stop_words is False.
        """
        counts = wordhandler.get_word_counts(
            "the cat and the hat",
            ignore_case=True,
            ignore_stop_words=False,
            stopwords_language="english",
            get_bigrams=False,
            get_trigrams=False,
        )

        unique_words = dict(counts["unique_words"])
        self.assertEqual(unique_words["the"], 2)
        self.assertEqual(unique_words["and"], 1)
        self.assertEqual(unique_words["cat"], 1)
        self.assertEqual(unique_words["hat"], 1)

    def test_punctuation_is_not_counted_as_words(self):
        """
        Standalone punctuation should not appear in unique word counts.
        """
        counts = wordhandler.get_word_counts(
            "hello, world! hello.",
            ignore_case=True,
            ignore_stop_words=False,
            stopwords_language="english",
            get_bigrams=False,
            get_trigrams=False,
        )

        unique_words = dict(counts["unique_words"])
        self.assertEqual(unique_words["hello"], 2)
        self.assertEqual(unique_words["world"], 1)
        self.assertNotIn(",", unique_words)
        self.assertNotIn("!", unique_words)
        self.assertNotIn(".", unique_words)

    def test_bigrams_are_counted(self):
        """
        Bigrams should be counted in sequence order.
        """
        counts = wordhandler.get_word_counts(
            "red fish blue fish",
            ignore_case=True,
            ignore_stop_words=False,
            stopwords_language="english",
            get_bigrams=True,
            get_trigrams=False,
        )

        bigrams = dict(counts["bigrams"])
        self.assertEqual(bigrams[("red", "fish")], 1)
        self.assertEqual(bigrams[("fish", "blue")], 1)
        self.assertEqual(bigrams[("blue", "fish")], 1)

    def test_trigrams_are_counted(self):
        """
        Trigrams should be counted in sequence order.
        """
        counts = wordhandler.get_word_counts(
            "one two three four",
            ignore_case=True,
            ignore_stop_words=False,
            stopwords_language="english",
            get_bigrams=False,
            get_trigrams=True,
        )

        trigrams = dict(counts["trigrams"])
        self.assertEqual(trigrams[("one", "two", "three")], 1)
        self.assertEqual(trigrams[("two", "three", "four")], 1)