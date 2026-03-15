let start = document.getElementById("start");
let thanks = document.getElementById("thanks");
let label = document.getElementById("label");
let ask = document.getElementById("ask");
let div = document.getElementById("div");
let next = document.getElementById("next");
let sub = document.getElementById("sub");
let timer = document.getElementById("timer");

var i = 1;
var l = ['Нулевой элемент.',
		 'Вам легче выразить свои мысли вслух, чем изложить их в письменной форме?',
		 'При принятии решений вы в первую очередь опираетесь на факты и конкретную информацию?',
		 'При решении проблем вы стараетесь быть максимально объективным, даже если это задевает чьи‑то чувства?',
		 'Вы любите планировать свой день и придерживаться расписания?',
		 'Вы чувствуете прилив энергии после общения с большой компанией людей?',
		 'Вам нравится сосредотачиваться на том, что происходит здесь и сейчас?',
		 'Вам проще дать логичный совет другу, чем посочувствовать его эмоциям?',
		 'Вам некомфортно, если важные решения остаются открытыми надолго?',
		 'Вы часто начинаете разговор первым в незнакомой компании?',
		 'Вы обращаете внимание на мелкие детали, которые другие могут не заметить?',
		 'В споре вы цените чёткие аргументы выше, чем стремление сохранить хорошие отношения?',
		 'Вы чувствуете себя увереннее, когда всё вокруг упорядочено и структурировано?',
		 'Вам комфортнее работать в команде, чем в одиночку?',
		 'Вы предпочитаете чётко структурированные инструкции, а не общие идеи?',
		 'Вы считаете, что справедливость важнее дипломатии?',
		 'Вы обычно завершаете начатые дела до дедлайна, а не оставляете их на последний момент?',
		 'Вы предпочитаете действовать сразу, а потом уже обдумывать свои действия?',
		 'Вас больше интересует практическое применение знаний, чем абстрактные теории?',
		 'При выборе между двумя вариантами вы чаще анализируете плюсы и минусы, а не то, как это повлияет на людей?',
		 'Вам нравится иметь чёткий план даже для отдыха и развлечений?'];
window.answers = [0, 0, 0, 0];

start.addEventListener('click', () => {
	start.style.display = 'none';
	thanks.style.display = 'none';
	div.style.display = 'grid';
	next.style.display = 'grid';
	window.start_time = new Date();
	ask.placeholder = l[i];
	label.innerHTML = l[i];
});
next.addEventListener('click', () => {
	if (ask.value != "") {
		if (i < 20) {
			if (ask.value == "Да") {
				window.answers[i % 4] = window.answers[i % 4] + 1;
			}
			i = i + 1;
			ask.placeholder = l[i];
			label.innerHTML = l[i];
		} else {
			var v1 = ""; var v2 = ""; var v3 = ""; var v4 = "";
			if (window.answers[1] >= 3) { v1 = "E" } else { v1 = "I" }
			if (window.answers[2] >= 3) { v2 = "S" } else { v2 = "N" }
			if (window.answers[3] >= 3) { v3 = "T" } else { v3 = "F" }
			if (window.answers[0] >= 3) { v4 = "J" } else { v4 = "P" }
			next.style.display = 'none';
			div.style.display = 'none';
			sub.style.display = 'grid';
			ask.value = v1 + v2 + v3 + v4;
			alert(window.answers); alert(ask.value);
			timer.value = (new Date() - window.start_time) / 1000;
		}
		ask.value = "";
		//alert(window.answers)
	}
});