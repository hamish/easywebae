﻿/*
Copyright (c) 2003-2009, CKSource - Frederico Knabben. All rights reserved.
For licensing, see LICENSE.html or http://ckeditor.com/license
*/

(function(){var a=function(c,d){return c._.modes&&c._.modes[d||c.mode];},b;CKEDITOR.plugins.add('editingblock',{init:function(c){if(!c.config.editingBlock)return;c.on('themeSpace',function(d){if(d.data.space=='contents')d.data.html+='<br>';});c.on('themeLoaded',function(){c.fireOnce('editingBlockReady');});c.on('uiReady',function(){c.setMode(c.config.startupMode);if(c.config.startupFocus)c.focus();});c.on('afterSetData',function(){if(!b){function d(){b=true;a(c).loadData(c.getData());b=false;};if(c.mode)d();else c.on('mode',function(){d();c.removeListener('mode',arguments.callee);});}});c.on('beforeGetData',function(){if(!b&&c.mode){b=true;c.setData(a(c).getData());b=false;}});c.on('getSnapshot',function(d){if(c.mode)d.data=a(c).getSnapshotData();});c.on('loadSnapshot',function(d){if(c.mode)a(c).loadSnapshotData(d.data);});c.on('mode',function(d){d.removeListener();c.container.on('focus',function(){c.focus();});c.fireOnce('instanceReady');CKEDITOR.fire('instanceReady',null,c);});}});CKEDITOR.editor.prototype.mode='';CKEDITOR.editor.prototype.addMode=function(c,d){d.name=c;(this._.modes||(this._.modes={}))[c]=d;};CKEDITOR.editor.prototype.setMode=function(c){var d,e=this.getThemeSpace('contents'),f=this.checkDirty();if(this.mode){if(c==this.mode)return;var g=a(this);d=g.getData();g.unload(e);this.mode='';}e.setHtml('');var h=a(this,c);if(!h)throw '[CKEDITOR.editor.setMode] Unknown mode "'+c+'".';if(!f)this.on('mode',function(){this.resetDirty();this.removeListener('mode',arguments.callee);});h.load(e,typeof d!='string'?this.getData():d);};CKEDITOR.editor.prototype.focus=function(){var c=a(this);if(c)c.focus();};})();CKEDITOR.config.startupMode='wysiwyg';CKEDITOR.config.startupFocus=false;CKEDITOR.config.editingBlock=true;
