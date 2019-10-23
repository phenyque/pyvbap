"""
Script that aids in the creation of JSON files containing the speaker setups.
"""

import json


def sanitised_input(msg, type_=None, min_=None, max_=None, range_=None):
    """
    Get input from user until they entered something valid. Based on:
    https://stackoverflow.com/questions/23294658/asking-the-user-for-input-until-they-give-a-valid-response
    """
    if min_ is not None and max_ is not None and max_ < min_:
        raise ValueError("min_ must be less than or equal to max_.")

    while True:
        prompt = input(msg)

        if type_ is not None:
            try:
                prompt = type_(prompt)
            except ValueError:
                print("Input type must be {0}.".format(type_.__name__))
                continue

        if max_ is not None and prompt > max_:
            print("Input must be less than or equal to {0}.".format(max_))
        elif min_ is not None and prompt < min_:
            print("Input must be greater than or equal to {0}.".format(min_))
        elif range_ is not None and prompt not in range_:
            if isinstance(range_, range):
                template = "Input must be between {0.start} and {0.stop}."
                print(template.format(range_))
            else:
                template = "Input must be {0}."
                if len(range_) == 1:
                    print(template.format(*range_))
                else:
                    print(template.format(" or ".join((", ".join(map(str, 
                        range_[:-1])), str(range_[-1])))))
        else:
            return prompt


if __name__ == '__main__':
    setup = dict()
    print('This script creates JSON files for your custom speaker setup.')

    # for now only 2D setups
    print('Note: for now, only two-dimensional setups are possible.')
    setup['height'] = False

    setup['name'] = sanitised_input('Enter the name of your setup.', str)
    num_spkrs = sanitised_input('How many speakers does your setup use?', int, min_=1)
    spkrs = list()


    for i in range(num_spkrs):
        spkrs.append(sanitised_input('Enter azimuth angle for speaker {} (in (-180, 180]).', int, min_=-179, max_=180))
    setup['positions'] = spkrs
    has_bounds = sanitised_input('Does your setup have bounds for the panning angle? (y/n)', str.lower, range_=['y', 'n'])
    if has_bounds:
        lower_bound = sanitised_input('Enter lower bound (in (-180, 0])', int, min_=-179, max_=0)
        upper_bound = sanitised_input('Enter upper bound (in [0, 180])', int, min_=0, max_= 180)
        setup['bounds'] = [lower_bound, upper_bound]

    print('Input setup looks like this:')
    print(json.dumps(setup))
    do_write = sanitised_input('Write to file? (y/n)', str.lower, range_=['y', 'n'])
    if do_write:
        filename = sanitised_input('Enter filename.', str)
        with open(filename, 'w') as f:
            json.dump(setup, f)
        print('Done!')
    else:
        print('Abort!')
