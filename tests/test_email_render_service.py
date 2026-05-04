from types import SimpleNamespace
from app.services.email_render import render_simple_template, render_campaign_content


def test_render_subject_html_text_and_missing_variables():
    out, missing = render_simple_template('Hello {{ name }} {{unknown}}', {'name': 'Ada'})
    assert out == 'Hello Ada '
    assert missing == ['unknown']


def test_render_campaign_override_variables():
    t = SimpleNamespace(subject='Hi {{name}}', preheader='P {{x}}', html_body='<p>{{name}}</p>', text_body='{{name}}', variables_json={'name': 'Base', 'x': 'x'})
    c = SimpleNamespace(subject_override=None, preheader_override=None, variables_json={'name': 'Campaign'})
    r = render_campaign_content(t, c, {'name': 'Override'})
    assert r['subject'] == 'Hi Override'
    assert r['html_body'] == '<p>Override</p>'
    assert r['text_body'] == 'Override'
