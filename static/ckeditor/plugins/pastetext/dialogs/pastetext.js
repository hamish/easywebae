/*
Copyright (c) 2003-2009, CKSource - Frederico Knabben. All rights reserved.
For licensing, see LICENSE.html or http://ckeditor.com/license
*/

(function(){CKEDITOR.dialog.add('pastetext',function(a){var b='cke_'+CKEDITOR.tools.getNextNumber();return{title:a.lang.pasteText.title,minWidth:400,minHeight:330,onShow:function(){CKEDITOR.document.getById(b).setValue('');},onOk:function(){var c=CKEDITOR.document.getById(b).getValue();this.restoreSelection();this.clearSavedSelection();this.getParentEditor().insertText(c);},contents:[{label:a.lang.common.generalTab,elements:[{type:'html',id:'pasteMsg',html:'<div style="white-space:normal;width:340px;">'+a.lang.clipboard.pasteMsg+'</div>'},{type:'html',id:'content',style:'width:340px;height:170px',html:'<textarea id="'+b+'" style="'+'width:346px;'+'height:170px;'+'border:1px solid black;'+'background-color:white">'+'</textarea>'}]}]};});})();
