# -*- coding: utf-8 -*-
#
# This file is part of OpenMediaVault.
#
# @license   http://www.gnu.org/licenses/gpl.html GPL Version 3
# @author    Volker Theile <volker.theile@openmediavault.org>
# @copyright Copyright (c) 2009-2017 Volker Theile
#
# OpenMediaVault is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# OpenMediaVault is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with OpenMediaVault. If not, see <http://www.gnu.org/licenses/>.
__all__ = [
	"flatten",
	"DotDict",
	"DotCollapsedDict"
]

def flatten(d, seperator="."):
	"""
	Collapses a multi-dimensional Python dictionary into a single dimension
	Python dictionary using dot notation for the keys.
	``
	Example:
	{'x':1, 'a': {'b': {'c': 100}}, 'k': [1, 2, 3]}
	Result:
	{'x':1, 'a.b.c': 100, 'k.0': 1, 'k.1': 2, 'k.2': 3}
	``
	:param d:			The Python dictionary to flatten.
	:param seperator:	The character used as separator. Defaults to '.'.
	:returns:			A single-dimensional Python dictionary.
	"""
	assert(isinstance(d, dict))
	result = {}

	def _process_item(value, key=""):
		if isinstance(value, dict):
			for item_key, item_value in value.items():
				_process_item(item_value, key + item_key + seperator)
		elif isinstance(value, list):
			for item_key, item_value in enumerate(value):
				_process_item(item_value, key + str(item_key) + seperator)
		else:
			result[key[:-1]] = value

	_process_item(d)
	return result

class DotDict(dict):
	def __init__(self, d=None):
		if d is None:
			return
		if not isinstance(d, dict):
			raise TypeError("Expected dictionary.")
		for key, value in d.items():
			self.__setitem__(key, value)

	def setdefault(self, key, default):
		if not key in self:
			self[key] = default
		return self[key]

	def get(self, key, default=None):
		if DotDict.__contains__(self, key):
			return DotDict.__getitem__(self, key)
		return default

	def __getitem__(self, key):
		if key is None or "." not in key:
			return dict.__getitem__(self, key)
		first, rest = key.split(".", 1)
		branch = dict.__getitem__(self, first)
		if isinstance(branch, list):
			first, rest = rest.split(".", 1)
			if not first.isdigit():
				raise KeyError("Key '%s' must be a number".format(first))
			branch = branch[int(first)]
		if not isinstance(branch, DotDict):
			raise KeyError("Can't get '%s' in '%s' (%s)".format(
				rest, first, str(branch)))
		return branch[rest]

	__getattr__ = __getitem__

	def __setitem__(self, key, value):
		if not key is None and "." in key:
			first, rest = key.split(".", 1)
			branch = self.setdefault(first, DotDict())
			if not isinstance(branch, DotDict):
				branch = DotDict()
			branch[rest] = value
		else:
			if isinstance(value, list):
				value = [DotDict(item) if isinstance(item, dict) else item
					for item in value]
			if isinstance(value, dict) and not isinstance(value, DotDict):
				value = DotDict(value)
			dict.__setitem__(self, key, value)

	__setattr__ = __setitem__

	def __contains__(self, key):
		if key is None or not "." in key:
			return dict.__contains__(self, key)
		first, rest = key.split(".", 1)
		if not dict.__contains__(self, first):
			return False
		branch = dict.__getitem__(self, first)
		if not isinstance(branch, DotDict):
			return False
		return rest in branch

class DotCollapsedDict(dict):
	"""
	Collapses a multi-dimensional Python dictionary into a single dimension
	Python dictionary using dot notation for the keys.
	``
	Example:
	{'x':1, 'a': {'b': {'c': 100}}, 'k': [1, 2, 3]}
	Result:
	{'x':1, 'a.b.c': 100, 'k[0]': 1, 'k[1]': 2, 'k[2]': 3}
	``
	"""

	def __init__(self, d=None):
		"""
		:param d: The Python dictionary to collapse.
		"""
		if d is None:
			return
		if not isinstance(d, dict):
			raise TypeError("Expected dictionary.")
		self._process_item(d)

	def _process_item(self, value, key=""):
		if isinstance(value, dict):
			for item_key, item_value in value.items():
				new_key = "%s.%s" % (key, item_key) if key else item_key
				self._process_item(item_value, new_key)
		elif isinstance(value, list):
			for item_key, item_value in enumerate(value):
				new_key = "%s[%d]" % (key, item_key)
				self._process_item(item_value, new_key)
		else:
			dict.__setitem__(self, key, value)
