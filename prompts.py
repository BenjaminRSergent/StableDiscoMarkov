import copy
import re
import random
import numpy as np
import utils


class UserPrompt:
    def __init__(self, prompt, args, img_url, date_str):
        self.prompt = prompt
        self.args = args
        self.img_url = img_url
        self.date_str = date_str

    def get_prompt_with_args(self):
        return f"{self.prompt} {' '.join(self.args)}"

    def __str__(self):
        return f"Date:{self.date_str}\nPrompt: {self.prompt}\nImage Url: {self.img_url}"


class ArgSelector:
    def __init__(self, arg_val_cnt, total_prompt_cnt):
        self._param_freq = {param: sum(val.values()) / total_prompt_cnt for param, val in arg_val_cnt.items()}
        self._arg_val_freq = dict(copy.deepcopy(arg_val_cnt))
        for param, vals_cnts in self._arg_val_freq.items():
            total_cnt = sum(vals_cnts.values())
            for param_val in vals_cnts:
                vals_cnts[param_val] /= total_cnt

    # prob_boost increases the chance of arguments to account for not always supporting them
    def get_random_args(self, prob_boost=10000.0):
        args = []
        for param, prob in self._param_freq.items():
            if random.random() < prob * prob_boost:
                value = self._choose_arg_value(param)
                args.append(f"{param} {value}")

        return ' '.join(args)

    def _choose_arg_value(self, param):
        freqs = self._arg_val_freq[param]
        keys = list(freqs.keys())
        probs = [freqs[key] for key in keys]
        return np.random.choice(keys, p=probs)


def arg_prompt_split(command):
    args = re.findall(r"--\w+ *=?\w+", command)
    prompt = re.sub('|'.join(args), "", command).strip()

    def split_key_val(arg):
        arg = re.sub(" +", " ", arg)
        split = re.split('[ =]', arg)
        if len(split) != 2:
            return []
        return split[0], split[1]

    key_val_pairs = utils.remove_none_and_dups([split_key_val(arg) for arg in args])

    args = {key: val for key, val in key_val_pairs if len(key_val_pairs) == 2}

    return prompt, args
