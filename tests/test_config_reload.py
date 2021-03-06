# vim:fileencoding=utf-8:noet
from __future__ import unicode_literals
import powerline as powerline_module
from time import sleep
from tests import TestCase
from tests.lib import replace_item
from tests.lib.config_mock import swap_attributes, get_powerline, pop_events, add_watcher_events
from copy import deepcopy


config = {
	'config': {
		'common': {
			'dividers': {
				"left": {
					"hard": ">>",
					"soft": ">",
				},
				"right": {
					"hard": "<<",
					"soft": "<",
				},
			},
			'spaces': 0,
			'interval': 0,
			'watcher': 'test',
		},
		'ext': {
			'test': {
				'theme': 'default',
				'colorscheme': 'default',
			},
		},
	},
	'colors': {
		'colors': {
			"col1": 1,
			"col2": 2,
			"col3": 3,
			"col4": 4,
		},
		'gradients': {
		},
	},
	'colorschemes/test/default': {
		'groups': {
			"str1": {"fg": "col1", "bg": "col2", "attr": ["bold"]},
			"str2": {"fg": "col3", "bg": "col4", "attr": ["underline"]},
		},
	},
	'colorschemes/test/2': {
		'groups': {
			"str1": {"fg": "col2", "bg": "col3", "attr": ["bold"]},
			"str2": {"fg": "col1", "bg": "col4", "attr": ["underline"]},
		},
	},
	'themes/test/default': {
		'segments': {
			"left": [
				{
					"type": "string",
					"contents": "s",
					"highlight_group": ["str1"],
				},
				{
					"type": "string",
					"contents": "g",
					"highlight_group": ["str2"],
				},
			],
			"right": [
			],
		},
	},
	'themes/test/2': {
		'segments': {
			"left": [
				{
					"type": "string",
					"contents": "t",
					"highlight_group": ["str1"],
				},
				{
					"type": "string",
					"contents": "b",
					"highlight_group": ["str2"],
				},
			],
			"right": [
			],
		},
	},
}


class TestConfigReload(TestCase):
	def assertAccessEvents(self, *args):
		self.assertEqual(set(pop_events()), set(args))

	def test_noreload(self):
		with get_powerline(run_once=True) as p:
			with replace_item(globals(), 'config', deepcopy(config)):
				self.assertEqual(p.render(), '<1 2 1> s<2 4 False>>><3 4 4>g<4 False False>>><None None None>')
				self.assertAccessEvents('config', 'colors', 'colorschemes/default', 'colorschemes/test/__main__', 'colorschemes/test/default', 'themes/test/default')
				config['config']['common']['spaces'] = 1
				add_watcher_events(p, 'config', wait=False, interval=0.05)
				# When running once thread should not start
				self.assertEqual(p.render(), '<1 2 1> s<2 4 False>>><3 4 4>g<4 False False>>><None None None>')
				self.assertAccessEvents()
				self.assertEqual(p.logger._pop_msgs(), [])
		# Without the following assertion test_reload_colors may fail for 
		# unknown reason (with AssertionError telling about “config” accessed 
		# one more time then needed)
		pop_events()

	def test_reload_main(self):
		with get_powerline(run_once=False) as p:
			with replace_item(globals(), 'config', deepcopy(config)):
				self.assertEqual(p.render(), '<1 2 1> s<2 4 False>>><3 4 4>g<4 False False>>><None None None>')
				self.assertAccessEvents('config', 'colors', 'colorschemes/default', 'colorschemes/test/__main__', 'colorschemes/test/default', 'themes/test/default')

				config['config']['common']['spaces'] = 1
				add_watcher_events(p, 'config')
				self.assertEqual(p.render(), '<1 2 1> s <2 4 False>>><3 4 4>g <4 False False>>><None None None>')
				self.assertAccessEvents('config')
				self.assertEqual(p.logger._pop_msgs(), [])

				config['config']['ext']['test']['theme'] = 'nonexistent'
				add_watcher_events(p, 'config')
				self.assertEqual(p.render(), '<1 2 1> s <2 4 False>>><3 4 4>g <4 False False>>><None None None>')
				self.assertAccessEvents('config', 'themes/test/nonexistent')
				# It should normally handle file missing error
				self.assertEqual(p.logger._pop_msgs(), ['exception:test:powerline:Failed to create renderer: themes/test/nonexistent'])

				config['config']['ext']['test']['theme'] = 'default'
				add_watcher_events(p, 'config')
				self.assertEqual(p.render(), '<1 2 1> s <2 4 False>>><3 4 4>g <4 False False>>><None None None>')
				self.assertAccessEvents('config', 'themes/test/default')
				self.assertEqual(p.logger._pop_msgs(), [])

				config['config']['ext']['test']['colorscheme'] = 'nonexistent'
				add_watcher_events(p, 'config')
				self.assertEqual(p.render(), '<1 2 1> s <2 4 False>>><3 4 4>g <4 False False>>><None None None>')
				self.assertAccessEvents('config', 'colorschemes/nonexistent', 'colorschemes/test/__main__', 'colorschemes/test/nonexistent')
				# It should normally handle file missing error
				self.assertEqual(p.logger._pop_msgs(), [
					'exception:test:powerline:Failed to load colorscheme: colorschemes/nonexistent',
					'exception:test:powerline:Failed to load colorscheme: colorschemes/test/__main__',
					'exception:test:powerline:Failed to load colorscheme: colorschemes/test/nonexistent',
					'exception:test:powerline:Failed to create renderer: colorschemes/test/nonexistent'
				])

				config['config']['ext']['test']['colorscheme'] = '2'
				add_watcher_events(p, 'config')
				self.assertEqual(p.render(), '<2 3 1> s <3 4 False>>><1 4 4>g <4 False False>>><None None None>')
				self.assertAccessEvents('config', 'colorschemes/2', 'colorschemes/test/__main__', 'colorschemes/test/2')
				self.assertEqual(p.logger._pop_msgs(), [])

				config['config']['ext']['test']['theme'] = '2'
				add_watcher_events(p, 'config')
				self.assertEqual(p.render(), '<2 3 1> t <3 4 False>>><1 4 4>b <4 False False>>><None None None>')
				self.assertAccessEvents('config', 'themes/test/2')
				self.assertEqual(p.logger._pop_msgs(), [])

				self.assertEqual(p.renderer.local_themes, None)
				config['config']['ext']['test']['local_themes'] = 'something'
				add_watcher_events(p, 'config')
				self.assertEqual(p.render(), '<2 3 1> t <3 4 False>>><1 4 4>b <4 False False>>><None None None>')
				self.assertAccessEvents('config')
				self.assertEqual(p.logger._pop_msgs(), [])
				self.assertEqual(p.renderer.local_themes, 'something')
		pop_events()

	def test_reload_unexistent(self):
		with get_powerline(run_once=False) as p:
			with replace_item(globals(), 'config', deepcopy(config)):
				self.assertEqual(p.render(), '<1 2 1> s<2 4 False>>><3 4 4>g<4 False False>>><None None None>')
				self.assertAccessEvents('config', 'colors', 'colorschemes/default', 'colorschemes/test/__main__', 'colorschemes/test/default', 'themes/test/default')

				config['config']['ext']['test']['colorscheme'] = 'nonexistentraise'
				add_watcher_events(p, 'config')
				# It may appear that p.logger._pop_msgs() is called after given 
				# exception is added to the mesagges, but before config_loader 
				# exception was added (this one: 
				# “exception:test:config_loader:Error while running condition 
				# function for key colorschemes/test/nonexistentraise: 
				# fcf:colorschemes/test/nonexistentraise”).
				# sleep(0.1)
				self.assertEqual(p.render(), '<1 2 1> s<2 4 False>>><3 4 4>g<4 False False>>><None None None>')
				# For colorschemes/{test/,}*raise find_config_file raises 
				# IOError, but it does not do so for colorschemes/test/__main__, 
				# so powerline is trying to load this, but not other 
				# colorschemes/*
				self.assertAccessEvents('config', 'colorschemes/test/__main__')
				self.assertIn('exception:test:powerline:Failed to create renderer: fcf:colorschemes/test/nonexistentraise', p.logger._pop_msgs())

				config['colorschemes/nonexistentraise'] = {}
				config['colorschemes/test/nonexistentraise'] = {
					'groups': {
						"str1": {"fg": "col1", "bg": "col3", "attr": ["bold"]},
						"str2": {"fg": "col2", "bg": "col4", "attr": ["underline"]},
					},
				}
				while not p._will_create_renderer():
					sleep(0.1)
				self.assertEqual(p.render(), '<1 3 1> s<3 4 False>>><2 4 4>g<4 False False>>><None None None>')
				# Same as above
				self.assertAccessEvents('colorschemes/nonexistentraise', 'colorschemes/test/nonexistentraise', 'colorschemes/test/__main__')
				self.assertEqual(p.logger._pop_msgs(), [])
		pop_events()

	def test_reload_colors(self):
		with get_powerline(run_once=False) as p:
			with replace_item(globals(), 'config', deepcopy(config)):
				self.assertEqual(p.render(), '<1 2 1> s<2 4 False>>><3 4 4>g<4 False False>>><None None None>')
				self.assertAccessEvents('config', 'colors', 'colorschemes/default', 'colorschemes/test/__main__', 'colorschemes/test/default', 'themes/test/default')

				config['colors']['colors']['col1'] = 5
				add_watcher_events(p, 'colors')
				self.assertEqual(p.render(), '<5 2 1> s<2 4 False>>><3 4 4>g<4 False False>>><None None None>')
				self.assertAccessEvents('colors')
				self.assertEqual(p.logger._pop_msgs(), [])
		pop_events()

	def test_reload_colorscheme(self):
		with get_powerline(run_once=False) as p:
			with replace_item(globals(), 'config', deepcopy(config)):
				self.assertEqual(p.render(), '<1 2 1> s<2 4 False>>><3 4 4>g<4 False False>>><None None None>')
				self.assertAccessEvents('config', 'colors', 'colorschemes/default', 'colorschemes/test/__main__', 'colorschemes/test/default', 'themes/test/default')

				config['colorschemes/test/default']['groups']['str1']['bg'] = 'col3'
				add_watcher_events(p, 'colorschemes/test/default')
				self.assertEqual(p.render(), '<1 3 1> s<3 4 False>>><3 4 4>g<4 False False>>><None None None>')
				self.assertAccessEvents('colorschemes/default', 'colorschemes/test/__main__', 'colorschemes/test/default')
				self.assertEqual(p.logger._pop_msgs(), [])
		pop_events()

	def test_reload_theme(self):
		with get_powerline(run_once=False) as p:
			with replace_item(globals(), 'config', deepcopy(config)):
				self.assertEqual(p.render(), '<1 2 1> s<2 4 False>>><3 4 4>g<4 False False>>><None None None>')
				self.assertAccessEvents('config', 'colors', 'colorschemes/default', 'colorschemes/test/__main__', 'colorschemes/test/default', 'themes/test/default')

				config['themes/test/default']['segments']['left'][0]['contents'] = 'col3'
				add_watcher_events(p, 'themes/test/default')
				self.assertEqual(p.render(), '<1 2 1> col3<2 4 False>>><3 4 4>g<4 False False>>><None None None>')
				self.assertAccessEvents('themes/test/default')
				self.assertEqual(p.logger._pop_msgs(), [])
		pop_events()

	def test_reload_theme_main(self):
		with replace_item(globals(), 'config', deepcopy(config)):
			config['config']['common']['interval'] = None
			with get_powerline(run_once=False) as p:
				self.assertEqual(p.render(), '<1 2 1> s<2 4 False>>><3 4 4>g<4 False False>>><None None None>')
				self.assertAccessEvents('config', 'colors', 'colorschemes/default', 'colorschemes/test/__main__', 'colorschemes/test/default', 'themes/test/default')

				config['themes/test/default']['segments']['left'][0]['contents'] = 'col3'
				add_watcher_events(p, 'themes/test/default', wait=False)
				self.assertEqual(p.render(), '<1 2 1> col3<2 4 False>>><3 4 4>g<4 False False>>><None None None>')
				self.assertAccessEvents('themes/test/default')
				self.assertEqual(p.logger._pop_msgs(), [])
				self.assertTrue(p._watcher._calls)
		pop_events()

	def test_run_once_no_theme_reload(self):
		with replace_item(globals(), 'config', deepcopy(config)):
			config['config']['common']['interval'] = None
			with get_powerline(run_once=True) as p:
				self.assertEqual(p.render(), '<1 2 1> s<2 4 False>>><3 4 4>g<4 False False>>><None None None>')
				self.assertAccessEvents('config', 'colors', 'colorschemes/default', 'colorschemes/test/__main__', 'colorschemes/test/default', 'themes/test/default')

				config['themes/test/default']['segments']['left'][0]['contents'] = 'col3'
				add_watcher_events(p, 'themes/test/default', wait=False)
				self.assertEqual(p.render(), '<1 2 1> s<2 4 False>>><3 4 4>g<4 False False>>><None None None>')
				self.assertAccessEvents()
				self.assertEqual(p.logger._pop_msgs(), [])
				self.assertEqual(p._watcher._calls, [])
		pop_events()


replaces = {}


def setUpModule():
	global replaces
	replaces = swap_attributes(globals(), powerline_module, replaces)


tearDownModule = setUpModule


if __name__ == '__main__':
	from tests import main
	main()
