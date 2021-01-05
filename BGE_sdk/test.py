# encoding: utf-8
from BGE_sdk.api import BGEApi

client_id = 'ULCKTNFLXaiDGrpXWhmNMgbeBfsDZE54CQIpRBjp'
client_secret = '4z5G6uKKrMy7AAxGwSJN21sVXEwRrXObR2j2rntoWS5eBoT17s9VVIwLv9dt8jI3qegYGgSqzZrsfPw2IqV0xS2h5bp72t5F9wJ6nDMI3KuVubjLfN6Ka670BTG6tBvF'
redirect_uri = 'http://test.cn'

# 'client_credentials', 'authorization_code', 'refresh_token'
grant_type = 'authorization_code'
auth_token = 'dvuNl6oVen1pj2UmY_YohQ'
code = 'dNlnPJEszalejZxIaN1D5ac8aa0vdP'

access_token = 'wEeFKL2JKdcUsC5Bbl7l2SSjgIPhAG'
refresh_token = 'vQoX7PBFLwkZYznGp3JWNYntTW1zQn'

s = BGEApi(client_id,
           client_secret,
           redirect_uri,
           grant_type,
           auth_token=auth_token
           )
# res = s.authorization_url(state='abc')

# res = s.get_access_token(code=code)
#
# res = s.refresh_token(refresh_token)

# res = s.get_model(access_token, 'X3Ab52da314cseD', 'E-F19323806495',
#                   )

# res = s.download_file(access_token, 'ods/microbiome/processed/profi'
#                                     'le/e1863.a1863.100.15711335316'
#                                     '99.855babe0.E-F19581820449.rxn'
#                                     '.relab.tsv',
#                       region='domestic', expiration_time=3600)

# res = s.upload_file(access_token)

# res = s.get_microbiome_gene_abundance(
#     access_token, 'E-F19323806495', 'IGC_9.9M', 'list')

# res = s.get_microbiome_func_abundance(
#     access_token, 'E-N19120161866', 'go')

# res = s.get_microbiome_taxon_abundance(
#     access_token, 'E-F19323806495', taxon_id='BT1,BT2,BT3,BT4',
#     page=1, limit=999)

# res = s.get_answer(access_token)

# res = s.get_response(access_token, 1)

# res = s.get_survey(access_token, 3)

# res = s.improve_sample_info(
#     access_token, 'E-L20109830201', library_layout=3, insert_size=250)

# res = s.register_sample(access_token, 'E-DEFG', 4, 'P-W19318644755')

res = s.get_sample(access_token, 'E-B19692615052')

# res = s.get_variants(
#     access_token, 'E-B19692615052', 'rs9', 'rs72554665', 'rs1', 'rs2')

# res = s.get_user_info(access_token)

print(res)
