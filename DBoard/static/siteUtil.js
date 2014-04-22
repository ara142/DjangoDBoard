/*///////////
fancy box
///////////*/

// setup modal content links
function setupModalLink(selectorString) {
	$(selectorString)
		.fancybox({
			autoSize: false,
			autoHeight: true,
			padding: 0,
			margin: 0,
			helpers: {
				overlay: {
					css: { "background": "rgba(128, 128, 128, .6)" }
				}
			}
		});
}

// programmatically pop up a div as modal
function showModal(selectorString) {
	$.fancybox({
		autoSize: false,
		autoHeight: true,
		padding: 0,
		margin: 0,
		helpers: {
			overlay: {
				css: { "background": "rgba(128, 128, 128, .6)" }
			}
		},
		content: $(selectorString).show()
	});
}

/*///////////
page setup 
///////////*/

/* image preload */

// add to array for custom image preload
var _customPreloadImgArr = new Array();
function preloadImgs() {

	// default images
	var defPreloadImgArr = [
		"../images/buttons/button.bg.png",
		"../images/buttons/button-hov.bg.png",
		"../images/buttons/button.bg.disable.png"
	];

	$(defPreloadImgArr).each(function () {
		$('<img />')[0].src = this;
	});

	// custom
	$(_customPreloadImgArr).each(function () {
		$('<img />')[0].src = this;
	});
}

/* page load events */

$(document).ready(function () {
	setupDocumentReady();
	preloadImgs();
});

$(window).load(function () {
	setupWindowLoad();
});