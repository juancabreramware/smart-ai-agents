from smart_agent.validation import answer_correct


def test_terminal_period_is_representational_noise():
    actual={'support':'24/7 for P1 incidents; business hours for standard tickets.','regions':['Frankfurt','Dublin']}
    expected={'support':'24/7 for P1 incidents; business hours for standard tickets','regions':['Frankfurt','Dublin']}
    assert answer_correct(actual,expected)


def test_support_field_may_omit_redundant_support_word():
    actual={'support':'24/7','regions':['Frankfurt']}
    expected={'support':'24/7 support','regions':['Frankfurt']}
    assert answer_correct(actual,expected)


def test_normalization_does_not_hide_real_support_change():
    actual={'support':'24/7','regions':['Frankfurt']}
    expected={'support':'24/7 for P1 incidents; business hours for standard tickets','regions':['Frankfurt','Dublin']}
    assert not answer_correct(actual,expected)


def test_value_fields_remain_structurally_strict():
    assert not answer_correct({'price':'$29 per month'},{'value':29})


def test_value_field_support_word_may_be_omitted_when_meaning_is_same():
    assert answer_correct({'value':'24/5'},{'value':'24/5 support'},'Professional support level?')


def test_affirmative_yes_no_answer_is_correct_when_expected_value_is_in_question():
    assert answer_correct({'value':'Yes'},{'value':'24/5 support'},'Does Professional have 24/5 support?')
    assert answer_correct({'value':'yes'},{'value':'24/7 support'},'Does Enterprise have 24/7 support?')
    assert answer_correct({'value':'true'},{'value':'Enterprise'},'Is SSO available on Enterprise?')


def test_affirmative_answer_does_not_match_unrelated_expected_value():
    assert not answer_correct({'value':'yes'},{'value':'Enterprise'},'Is SSO available on Professional?')


def test_serialized_identifier_matches_natural_language_policy_value():
    assert answer_correct({'value':'end_of_current_paid_billing_period'},{'value':'end of the current paid billing period'},'If I cancel, when does service end?')


def test_harmless_sentence_prefix_matches_policy_value():
    assert answer_correct({'value':'Enterprise support is 24/7 for P1 incidents; business hours for standard tickets.'},{'value':'24/7 for P1 incidents; business hours for standard tickets'},'Describe Enterprise support.')
