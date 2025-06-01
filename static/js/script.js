function see_menu (menu_button, menu, img) {
	if (menu.style.display == 'none') {
		menu.style.display = 'block';
		var button_class = menu_button.className;
		menu_button.className = button_class.replace(' ', ' pressed');
		img.setAttribute('src', 'static/img/menu_pressed.png');
	}
	else {
		menu.style.display = 'none';
		var button_class = menu_button.className;
		menu_button.className = button_class.replace('pressed', '');
		img.setAttribute('src', 'static/img/menu.png');
	}
}
function see_user (menu_button, menu) {
	if (menu.style.display == 'none') {
		menu.style.display = 'block';
		var button_class = menu_button.className;
		menu_button.className = button_class.replace(' ', ' pressed');
	}
	else {
		menu.style.display = 'none';
		var button_class = menu_button.className;
		menu_button.className = button_class.replace('pressed', '');
	}
}