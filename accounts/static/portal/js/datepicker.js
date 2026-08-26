document.addEventListener("DOMContentLoaded", function () {
    const fields = document.querySelectorAll(".portal-datepicker");

    const englishLocale = {
        days: [
            "Sunday",
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday"
        ],

        daysShort: [
            "Sun",
            "Mon",
            "Tue",
            "Wed",
            "Thu",
            "Fri",
            "Sat"
        ],

        daysMin: [
            "Su",
            "Mo",
            "Tu",
            "We",
            "Th",
            "Fr",
            "Sa"
        ],

        months: [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December"
        ],

        monthsShort: [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec"
        ],

        today: "Today",
        clear: "Clear",
        dateFormat: "yyyy-MM-dd",
        timeFormat: "HH:mm",
        firstDay: 0
    };


    fields.forEach(function (field) {

        if (field.dataset.datepickerReady === "true") {
            return;
        }

        const picker = new AirDatepicker(field, {
            locale: englishLocale,

            autoClose: true,

            dateFormat: "yyyy-MM-dd",

            view: "days",

            minView: "days",

            navTitles: {
                days: "MMMM yyyy",
                months: "Select month — yyyy",
                years: "yyyy1 - yyyy2"
            },

            onSelect({ formattedDate }) {
                field.value = formattedDate;
            }
        });

        field.dataset.datepickerReady = "true";


        /*
         * Clicking the navigation title changes:
         *
         * Days -> Months
         * Months -> Years
         */

        picker.$datepicker.addEventListener("click", function (event) {

            const title = event.target.closest(
                ".air-datepicker-nav--title"
            );

            if (!title) {
                return;
            }

            if (picker.currentView === "days") {
                picker.setCurrentView("months");
            }

            else if (picker.currentView === "months") {
                picker.setCurrentView("years");
            }
        });
    });
});