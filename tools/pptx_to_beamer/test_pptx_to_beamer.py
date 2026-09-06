import unittest
import xml.etree.ElementTree as ET

from pptx_to_beamer import NS, alternatives, escape_tex, overlay_spec, timing, visible_steps


def effect(step, cls, target):
    return {"step": step, "class": cls, "targets": [target]}


class AnimationTests(unittest.TestCase):
    def test_entrance_not_visible_before_click(self):
        self.assertEqual(visible_steps(["2"], [effect(2, "entr", "2")], 4), [2, 3, 4])

    def test_static_visible_initially(self):
        self.assertEqual(visible_steps(["3"], [effect(2, "entr", "2")], 4), [1, 2, 3, 4])

    def test_exit_reentry_and_final_handout(self):
        ev = [effect(2, "entr", "2"), effect(3, "exit", "2"), effect(5, "entr", "2")]
        self.assertEqual(visible_steps(["2"], ev, 6), [2, 5, 6])
        self.assertEqual(overlay_spec(visible_steps(["2"], ev, 6)), "2,5-6")

    def test_exit_without_entrance(self):
        self.assertEqual(visible_steps(["2"], [effect(3, "exit", "2")], 4), [1, 2])

    def test_group_and_child_visibility_intersect(self):
        ev = [effect(2, "entr", "group"), effect(4, "entr", "child")]
        self.assertEqual(visible_steps(["group", "child"], ev, 5), [4, 5])

    def test_click_boundaries_and_simultaneous_events(self):
        root = ET.fromstring(f'''<p:sld xmlns:p="{NS['p']}"><p:timing>
          <p:cTn presetClass="entr" presetID="2" nodeType="clickEffect"><p:spTgt spid="8"/></p:cTn>
          <p:cTn presetClass="entr" presetID="2" nodeType="withEffect"><p:spTgt spid="9"/></p:cTn>
          <p:cTn presetClass="exit" presetID="2" nodeType="clickEffect"><p:spTgt spid="8"/></p:cTn>
        </p:timing></p:sld>''')
        ev, count, issues = timing(root)
        self.assertEqual(count, 3)
        self.assertEqual([e['step'] for e in ev], [2, 2, 3])
        self.assertTrue(any('withEffect' in issue for issue in issues))

    def test_paragraph_animation_reported(self):
        root = ET.fromstring(f'''<p:sld xmlns:p="{NS['p']}"><p:cTn presetClass="entr" nodeType="clickEffect">
        <p:spTgt spid="1"><p:txEl><p:pRg st="0" end="0"/></p:txEl></p:spTgt></p:cTn></p:sld>''')
        self.assertTrue(any('段落' in issue for issue in timing(root)[2]))

    def test_alternate_content_is_not_duplicated(self):
        root = ET.fromstring(f'''<p:sld xmlns:p="{NS['p']}" xmlns:mc="{NS['mc']}">
          <mc:AlternateContent><mc:Choice><p:sp id="chosen"/></mc:Choice>
          <mc:Fallback><p:sp id="fallback"/></mc:Fallback></mc:AlternateContent></p:sld>''')
        self.assertEqual([e.get('id') for e in alternatives(root)], ['chosen'])

    def test_source_text_cannot_be_tex_instructions(self):
        self.assertEqual(escape_tex(r'\input{secret}%'), r'\textbackslash{}input\{secret\}\%')


if __name__ == '__main__':
    unittest.main()
