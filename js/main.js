
/*!
 * Run a callback function after scrolling has stopped
 * (c) 2017 Chris Ferdinandi, MIT License, https://gomakethings.com
 * @param  {Function} callback The function to run after scrolling
 */
var scrollStop = function (callback) {

	// Make sure a valid callback was provided
	if (!callback || typeof callback !== 'function') return;

	// Setup scrolling variable
	var isScrolling;

	// Listen for scroll events
	window.addEventListener('scroll', function (event) {

		// Clear our timeout throughout the scroll
		window.clearTimeout(isScrolling);

		// Set a timeout to run after scrolling ends
		isScrolling = setTimeout(function() {

			// Run the callback
			callback();

		}, 66);

	}, false);

};
$(function () {

	$('.sections-nav-link').click(function () {
		$('body').removeClass('sections-nav-in');
	});

	$('.sections-nav-toggler').click(function () {
		$('body').toggleClass('sections-nav-in');
	});
});

$(function () {
	normalizeCarouselItems();

	window.addEventListener('resize', function () {
		normalizeCarouselItems();
	});

	function normalizeCarouselItems() {
		$('.carousel').each(function () {
			var $items = $(this).find('.carousel-item');
			$items.css('min-height', 0);
			var maxHeight = 0;
			$items.each(function () {
				var height = $(this).height();
				if (height > maxHeight) {
					maxHeight = height;
				}
			});

			$items.css('min-height', maxHeight);
		});
	}
});

$(function () {
	$('[data-toggle="tooltip"]').tooltip();

	$('.preview-theme').click(function () {
		$('link')[1].href = $(this).data('theme');
		var imgSrcData = $(this).data('theme-bg') === 'light' ? 'dark-src' : 'light-src';
		$('img[data-' + imgSrcData + ']').each(function () {
			$(this).attr('src', $(this).data(imgSrcData));
		});

		return false;
	});
});

// Bootstrap form validation example
(function() {
	'use strict';
	window.addEventListener('load', function() {
		var forms = document.getElementsByClassName('needs-validation');
		var validation = Array.prototype.filter.call(forms, function(form) {
			form.addEventListener('submit', function(event) {
				if (form.checkValidity() === false) {
					event.preventDefault();
					event.stopPropagation();
				}
				form.classList.add('was-validated');
			}, false);
		});
	}, false);
})();
