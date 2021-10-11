
# TODO initialize the mongodb database for testing purpose

"""
collection: ip_blacklist

{
    _id: ObjectID()
    lower: long     # lowest address for the blocked ip address
    higher: long    # highest address for the blocked ip address
    version: 4 or 6
}
"""