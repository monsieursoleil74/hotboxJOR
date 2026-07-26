
def move_elements_to_array_end(array, elements):
    return [e for e in array if e not in elements] + [e for e in elements]


def move_elements_to_array_begin(array, elements):
    return [e for e in elements] + [e for e in array if e not in elements]
