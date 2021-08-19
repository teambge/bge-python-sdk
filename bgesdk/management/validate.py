from validator import Required, In, validate, Length

from bgesdk.management.constants import TAB_CHOICES, LANGUAGE_CHOICES

language = [x[0] for x in LANGUAGE_CHOICES]
tab = [x[0] for x in TAB_CHOICES]


def validator_doc(doc_data):
    results = {}
    result_errors = {}
    validation = {
        'doc_tab': [Required, In(tab)],
        'model_id': [
            Required, Length(0, maximum=50), lambda x: isinstance(x, str)],
        'doc_content': [Required, lambda x: isinstance(x, list)]
    }
    res = validate(validation, doc_data)
    result_errors.update(res.errors)
    if isinstance(doc_data['doc_content'], list):
        for content in doc_data['doc_content']:
            validation = {
                'language': [Required, In(language)],
                'doc_name': [
                    Required, Length(0, maximum=50),
                    lambda x: isinstance(x, str)],
                'content_title': [
                    Required, Length(0, maximum=200),
                    lambda x: isinstance(x, str)],
                'developer': [
                    Length(0, maximum=50), lambda x: isinstance(x, str)],
                'brief_intro': [lambda x: isinstance(x, dict)],
                'method': [lambda x: isinstance(x, dict)],
                'model_evaluation': [lambda x: isinstance(x, dict)],
                'data_set_size': [lambda x: isinstance(x, dict)],
                'ethnicity': [lambda x: isinstance(x, dict)],
                'limitation': [lambda x: isinstance(x, dict)],
                'return_params': [lambda x: isinstance(x, dict)],
                'state_explain': [lambda x: isinstance(x, dict)],
                'example_result': [lambda x: isinstance(x, dict)],
                'ref': [lambda x: isinstance(x, list)]
            }
            content_res = validate(validation, content)
            result_errors.update(content_res.errors)
    valid = True
    if result_errors:
        valid = False
    results['errors'] = result_errors
    results['valid'] = valid
    return results