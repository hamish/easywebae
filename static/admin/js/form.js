/*** Functionality to highlight rows onmouseover, validate fields and show errors ***/

// global variables
var numErrors = 0;
var haltHighlighting = false;

// detect highlightable rows on load
dojo.addOnLoad(function () {
    var highlightRows = dojo.query("[class^=highlightable]");

    for (var i = 0; i < highlightRows.length; i++) {
        // add onmouseover events
        dojo.connect(highlightRows[i], "onmouseover", function () {
            toggleHighlight(this, true);
        });
        dojo.connect(highlightRows[i], "onmouseout", function () {
            toggleHighlight(this, false);
        });

        // add field events
        var fields = dojo.query("input", highlightRows[i]).concat(dojo.query("select", highlightRows[i]));

        for (var j = 0; j < fields.length; j++) {
            dojo.connect(fields[j], "onfocus", function () {
                toggleHighlight(this.parentNode.parentNode, true);
                haltHighlighting = true;
            });
            dojo.connect(fields[j], "onblur", function () {
                haltHighlighting = false;
                toggleHighlight(this.parentNode.parentNode, false);

                if (dojo.hasClass(this, "validate")) {
                    validate(this);
                }
            });
            if (dojo.hasClass(fields[j], "validate")) {
                var eventType = "onkeyup";
                if (fields[j].tagName == "SELECT") {
                    eventType = "onchange"
                }
                dojo.connect(fields[j], eventType, function () {
                    validate(this);
                });
            }
        }
    }

});

// highlight/unhighlight row and show/hide comments
function toggleHighlight(/*dom object*/row, /*boolean*/show) {
    if (haltHighlighting) return;

    if (show) {
        dojo.addClass(row, "highlight");

        if (!dojo.hasClass(row, "problem")) {
            showComment(row, "note");
        }
    } else {
        dojo.removeClass(row, "highlight");

        if (!dojo.hasClass(row, "problem")) {
            showComment(row, "placeholder");
        }
    }

}

function showComment(/*dom object*/row, /*string*/commentClass) {
    if (!commentClass) commentClass = "placeholder";
    var comments = dojo.query("[name^=comment]", row);

    for (var i = 0; i < comments.length; i++) {
        if (dojo.hasClass(comments[i], commentClass)) {
            dojo.removeClass(comments[i], "hidden");
        } else if (!dojo.hasClass(comments[i], "hidden")) {
            dojo.addClass(comments[i], "hidden");
        }
    }
}



// validation functions
function validateAll() {
    var valid = true;
    var fields = dojo.query("input").concat(dojo.query("select"));

    for (var i = fields.length-1; i >= 0; i--) { // iterate backwards so the topmost error gets focus
        if (dojo.hasClass(fields[i], "validate")) {
            valid = validate(fields[i]) && valid;
        }
    }

    return valid;
}

function validate(field) {
    var valid = true;
    var row = field.parentNode.parentNode;

    // validate field
    if (dojo.hasClass(field, "email")){
        valid = validateEmail(field);
    }
    else if (dojo.hasClass(field, "url")) {
        valid = validateUrl(field);
    }
    else if (dojo.hasClass(field, "price")) {
        valid = validatePrice(field);
    }
    else {
        valid = validateNotEmpty(field);
    }

    // highlight invalid field
    if (!valid) {
        if (!dojo.hasClass(row, "problem")) {
            numErrors++;
            dojo.addClass(row, "problem");
            // show error message
            showComment(row, "error");
        }

        // give field focus unless it's a file upload field
        if (!dojo.hasClass(field, "file")) {
            field.focus();
        }
    } else if (valid && dojo.hasClass(row, "problem")) {
        numErrors--;
        dojo.removeClass(row, "problem");
        // hide error message
        showComment(row, "note");
        toggleHighlight(row, false);
    }

    // show/hide submit button
    if (numErrors > 0) {
        toggleSubmit("cancel");
    }
    else {
        toggleSubmit("action");
    }

    return valid;
}

function validateEmail(field) {
    var regExp = /^([a-zA-Z0-9_.-])+@([a-zA-Z0-9_.-])+\.([a-zA-Z])+([a-zA-Z])+/;

    return regExp.test(field.value);
}

function validateUrl(field) {
    var regExp = new RegExp();
    regExp.compile("^[A-Za-z0-9-_/.]+$"); 

    return regExp.test(field.value);
}

function validatePrice(field) {
    return field.value.match(/^\d+\.+\d{2}$/);
}

function validateNotEmpty(field) {
    field.value.trim;
    return field.value != "";
}

// show submit if there are no errors, otherwise display error message instead
function toggleSubmit (/*boolean*/submitClass) {
    var submits = dojo.query("[name^=submit]");

    for (var i = 0; i < submits.length; i++) {
        if (dojo.hasClass(submits[i], submitClass)) {
            dojo.removeClass(submits[i], "hidden");
        } else if (!dojo.hasClass(submits[i], "hidden")) {
            dojo.addClass(submits[i], "hidden");
        }
    }
}

// submit form from an onclick event
function submitForm(form) {
    if (validateAll()) {
        form.submit();
    }
}