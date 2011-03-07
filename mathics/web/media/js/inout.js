/**
    Mathics: a general-purpose computer algebra system
    Copyright (C) 2011 Jan Pöschko

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
**/

function showSave() {
	requireLogin("You must login to save worksheets online.", function() {
		showPopup($('save'));
	});
}

function openWorksheet(name) {
	hidePopup();
	new Ajax.Request('/ajax/open/', {
		method: 'post',
		parameters: {
			'name': name
		},
		onSuccess: function(transport) {
			var response = transport.responseText.evalJSON();
			if ($('document').visible())
				setContent(response.content);
			else
				$('codetext').value = response.content;
		}
	})
}

function showOpen() {
	requireLogin("You must login to open online worksheets.", function() {
		new Ajax.Request('/ajax/getworksheets/', {
			method: 'get',
			onSuccess: function(transport) {
				var response = transport.responseText.evalJSON();
				var tbody = $('openFilelist'); 
				tbody.deleteChildNodes();
				response.worksheets.each(function(worksheet) {
					tbody.appendChild($E('tr', $E('td',
						$E('a', {'href': 'javascript:openWorksheet("' + worksheet.name + '")'},
							$T(worksheet.name)
						)
					)));
				});
				showPopup($('open'));
			}
		});
	});
}

function cancelSave() {
	hidePopup();
}

function cancelOpen() {
	hidePopup();
}

function save(overwrite) {
	if (!overwrite)
		overwrite = '';
	var content;
	if ($('document').visible())
		content = getContent();
	else
		content = $('codetext').value;
	submitForm('saveForm', '/ajax/save/', function(response) {
		if (!checkLogin(response))
			return;
		cancelSave();
		if (response.result == 'overwrite') {
			showDialog("Overwrite worksheet", "There already exists a worksheet with the name '" +
				response.form.values.name + "'. Do you want to overwrite it?",
				'Yes, overwrite it', 'No, cancel', function() {
					save(true);
				});
		}
	}, {
		'content': content,
		'overwrite': overwrite
	});
}

function switchCode() {
	if ($('document').visible()) {
		$('document').hide();
		var content = getContent();
		$('codetext').value = content;
		$('code').show();
		$('codelink').setText("Interactive mode");
	} else {
		var content = $('codetext').value;
		setContent(content);
		function load() {
			$('code').hide();
			$('document').show();
			$('codelink').setText("View/edit code");
		}
		load();
	}
}

function getContent() {
	var queries = [];
	$('queries').childElements().each(function(query) {
		var item = {};
		var request = query.select('textarea.request')[0].getText();
		item.request = request;
		var results = [];
		query.select('ul.out').each(function(out) {
			var outs = [];
			out.select('li.message, li.print').each(function(outMsg) {
				var text = DOMtoString(outMsg);
				var message = outMsg.hasClassName('message');
				var prefix = '';
				if (message) {
					prefix = text.substr(0, text.indexOf(': '));
					text = text.substr(text.indexOf(': ') + 2);
				}
				outs.push({'message': message, 'prefix': prefix, 'text': text});
			});
			var result = out.select('li.result');
			if (result.length > 0)
				result = DOMtoString(result[0]);
			else
				result = '';
			results.push({'out': outs, 'result': result});
		});
		item.results = results;
		queries.push(item);
	});
	var content = Object.toJSON(queries);
	
	return content;
}

function setContent(content) {
	$('queries').deleteChildNodes();
	
	$('welcome').hide();
	
	var queries = content.evalJSON();
	queries.each(function(item) {
		var li = createQuery(null, true, true);
		li.textarea.value = item.request;
		setResult(li.ul, item.results);
	});
	
	createSortable();
	
	refreshInputSizes();
	
	lastFocus = null;
	if ($('queries').lastChild)
		$('queries').lastChild.textarea.focus();
}

function createLink() {
	var queries = new Array();
	$('queries').childElements().each(function(query) {
		var text = query.select('textarea.request')[0].getText();
		queries[queries.length] = 'queries=' + encodeURIComponent(text);
	});
	var query = queries.join('&');
	location.hash = '#' + encodeURI(query);
}

function setQueries(queries) {
	var list = [];
	queries.each(function(query) {
		var li = createQuery(null, true, true);
		li.textarea.value = query;
		list.push({'li': li, 'query': query});
	});
	refreshInputSizes();
	function load(index) {
		if (index < list.length) {
			var item = list[index];
			submitQuery(item.li.textarea, item.query, function() {
				load(index + 1);
			});
		} else {
			createSortable();
			lastFocus = null;
			if ($('queries').lastChild)
				$('queries').lastChild.textarea.focus();
		}
	}
	load(0);	
}

function loadLink() {
	var hash = location.hash;
	if (hash && hash.length > 1) {
		var params = hash.slice(1).split('&');
		var queries = [];
		params.each(function(param) {
			if (param.startsWith('queries=')) {
				param = param.slice(8);
				param = decodeURIComponent(param);
				if (param != "")
					queries.push(param);
			}
		});
		setQueries(queries);
		return queries.length > 0;
	} else
		return false;
}

function showGallery() {
	setQueries([
	  '1 + 2 - x * 3 x / y',
	  'Sin[Pi]',
	  'N[E, 30]',
	  'Plot[{Sin[x], Cos[x]}, {x, -Pi, Pi}]',
	  'D[Sin[2x] + Log[x] ^ 2, x]',
	  'Integrate[Tan[x] ^ 5, x]',
	  'A = {{1, 2, 3}, {4, 5, 6}, {7, 8, 9}}; MatrixForm[A]',
	  'LinearSolve[A, {1, 1, 1}] // MatrixForm',
	  'Eigenvalues[A]',
	  '# ^ 2 & /@ Range[10]',
	  'Graphics[Table[{EdgeForm[{GrayLevel[0, 0.5]}], Hue[(-11+q+10r)/72, 1, 1, 0.6], Disk[(8-r){Cos[2Pi q/12], Sin [2Pi q/12]}, (8-r)/3]}, {r, 6}, {q, 12}]]'
	]);
}
