import markovify
import prompts
import utils
import random
import re

def get_markov_models(prompt_strs, state_size=3):
    prompt_minus_args = [prompts.arg_prompt_split(prompt)[0] for prompt in prompt_strs]
    markov_model = markovify.NewlineText(prompt_minus_args, state_size).compile()

    def reverse_command(prompt):
        return ' '.join(prompt.split(' ')[::-1])

    rev_commands = [reverse_command(prompt) for prompt in prompt_minus_args]
    rev_markov_model = markovify.NewlineText(rev_commands, state_size).compile()

    return markov_model, rev_markov_model

def make_markov_sentences(cnt, markov_model,
                                     arg_selector=None,
                          **kwargs):
    ret = []
    for _ in range(cnt):
        sent = markov_model.make_sentence(tries=200, **kwargs)
        if not sent:
            continue
        if arg_selector:
            args = arg_selector.get_random_args()
            sent = f"{sent} {args}"
        ret.append(sent)
        
    return ret

def make_markov_sentences_containing(num_mix_parts, key_word, 
                                     markov_model, rev_markov_model,
                                     arg_selector=None,
                                     key_word_replacement=None,
                                     mix_iters=2,
                                     **kwargs):
    forward_sentences = [markov_model.make_sentence_with_start(key_word, tries=200, **kwargs) for _ in range(num_mix_parts)]
    # Remove the first word to avoid doubling the keyword

    rev_sentences = [rev_markov_model.make_sentence_with_start(key_word, tries=200, **kwargs) for _ in range(num_mix_parts)]
    start_word = key_word
    if key_word_replacement:
        start_word = key_word_replacement
        forward_sentences = [re.sub(key_word, key_word_replacement, sentence) for sentence in forward_sentences]

    combined_sentences = []
    smaller_len = min(len(forward_sentences), len(rev_sentences))
    for _ in range(mix_iters):
        for start, end in zip(rev_sentences[:smaller_len], forward_sentences[:smaller_len]):
            # Remove the first word and reverse
            start = ' '.join(start.split(' ')[:0:-1])

            re.sub(start_word, "", end)
            args = arg_selector.get_random_args()
            sent = f"{start}{end} {args}"
            combined_sentences.append(sent)
        random.shuffle(forward_sentences)
    random.shuffle(combined_sentences)
    return utils.remove_none_and_dups(combined_sentences)
