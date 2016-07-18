/**
 * Created by juanjo on 12/03/16.
 */
//CKEDITOR.editorConfig = function (config) {
//    config.toolbarGroups = [
//        {name: 'document', groups: ['mode', 'document', 'doctools']},
//        {name: 'clipboard', groups: ['clipboard', 'undo']},
//        {name: 'editing', groups: ['find', 'selection', 'spellchecker', 'editing']},
//        {name: 'forms', groups: ['forms']},
//        '/',
//        {name: 'basicstyles', groups: ['basicstyles', 'cleanup']},
//        {name: 'paragraph', groups: ['list', 'indent', 'blocks', 'align', 'bidi', 'paragraph']},
//        {name: 'links', groups: ['links']},
//        {name: 'insert', groups: ['insert']},
//        '/',
//        {name: 'styles', groups: ['styles']},
//        {name: 'colors', groups: ['colors']},
//        {name: 'tools', groups: ['tools']},
//        {name: 'others', groups: ['others']},
//        {name: 'about', groups: ['about']}
//    ];
//
//    config.removeButtons = 'Save,NewPage,Preview,Print,Templates,SelectAll,Form,Checkbox,Radio,TextField,Textarea,Select,Button,ImageButton,HiddenField,Blockquote,CreateDiv,BidiLtr,BidiRtl,Language,Flash,Iframe,ShowBlocks';
//};

CKEDITOR.editorConfig = function( config ) {
	config.toolbar = [
		{ name: 'basicstyles', items: [ 'Bold', 'Italic', 'Underline', 'Strike', 'Subscript', 'Superscript', '-', 'RemoveFormat' ] },
		{ name: 'paragraph', items: [ 'NumberedList', 'BulletedList', '-', 'Outdent', 'Indent', '-', 'JustifyLeft', 'JustifyCenter', 'JustifyRight', 'JustifyBlock' ] },
		{ name: 'clipboard', items: [ 'Cut', 'Copy', 'Paste', 'PasteText', 'PasteFromWord', '-', 'Undo', 'Redo' ] },
		{ name: 'editing', items: [ 'Find', 'Replace', '-', 'Scayt' ] },
        { name: 'tools', items: [ 'Maximize' ] },
        { name: 'about', items: [ 'About' ] },
		'/',
		{ name: 'styles', items: [ 'Styles', 'Format', 'Font', 'FontSize' ] },
		{ name: 'colors', items: [ 'TextColor', 'BGColor' ] },
		{ name: 'links', items: [ 'Link', 'Unlink', 'Anchor' ] },
		{ name: 'insert', items: [ 'Image', 'Table', 'HorizontalRule', 'Smiley', 'SpecialChar', 'PageBreak' ] },
		{ name: 'document', items: [ 'Source' ] }
	];
};