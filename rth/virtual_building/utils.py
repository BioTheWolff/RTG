from rth.core.errors import MasterRouterError


def get_master_router(routers):
    """
        Get master route from all the routers

        :return master: master router instance
        :raises Exception: when no master or more than one is found
        """

    masters = []
    for i in range(len(routers)):
        r = routers[i]
        if r.internet is True:
            masters.append(i)

    # then we check if there is no master or more than one master
    if not masters:
        # no master router
        raise MasterRouterError(True)
    elif len(masters) > 1:
        raise MasterRouterError(False)
    else:
        return masters[0]


def smaller_of_list(given, return_index=False):
    if len(given) == 1:
        # only one path found
        return 0 if return_index else given[0]
    else:
        # we will loop to find the smaller list
        id_, length = None, None
        for j in range(len(given)):
            if j == 0:
                length = len(given[j])
                id_ = 0
            else:
                if len(given[j]) < length:
                    length = len(given[j])
                    id_ = j
        return id_ if return_index else given[id_]


def list_of_largest_of_list(given, return_index=False):
    if len(given) == 1:
        # only one path found
        return [0] if return_index else [given[0]]
    else:
        # we will loop to find the smaller list
        length = None
        dict_largest = {}
        for j in range(len(given)):
            if j == 0:
                length = given[j]
                dict_largest[0] = given[j]
            else:
                if given[j] == length:
                    # On par, we add to the list
                    dict_largest[j] = given[j]
                if given[j] > length:
                    # Bigger, we flush the list then add to it
                    dict_largest = {j: given[j]}

        return list(dict_largest.keys() if return_index else dict_largest.values())


def exists_and_matches(dictionary, key, value=True):
    return key in dictionary and dictionary[key] == value


def exists_and_not_none(dictionary, key):
    return key in dictionary and dictionary[key] is not None


def list_preferences_from_paths(paths, preferred):
    return [number_of_matching_in_list(preferred, p) for p in paths]


def number_of_matching_in_list(liste, elements):
    i = 0
    for e in elements:
        if e in liste:
            i += 1

    return i
