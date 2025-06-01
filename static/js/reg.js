const phoneInput = document.getElementById('tel');

// Регулярное выражение для проверки формата телефона
const phonePattern = /^\+7 \(\d{3}\) \d{3}-\d{2}-\d{2}$/;

// Функция форматирования номера
function formatPhone(value) {
    tel = value;
    if (tel.length == 15) {
        value += '-';
    }
    else {
		if (tel.length == 12) {
			value += '-';
		}
		else {
			if (tel.length == 7) {
				value += ') ';
			}
			else {
				if (tel.length == 1) {
					value = '+7 ('+value;
				}
			}
		}
	}

    return value;
}

// Обработка ввода
phoneInput.addEventListener('input', function() {
    const value = this.value;

    // Форматируем значение
    this.value = formatPhone(value);

    // Проверяем валидность
    if (phonePattern.test(value)) {
        this.classList.remove('invalid');
        this.classList.add('valid');
    } else {
        this.classList.remove('valid');
        this.classList.add('invalid');
    }
});
