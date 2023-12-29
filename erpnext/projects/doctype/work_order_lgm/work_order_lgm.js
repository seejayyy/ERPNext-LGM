// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Work Order LGM', {
	before_submit(frm){
		var ingredients_list = frm.doc["weighing_table_lgm"];
		var no_of_ingredients = frm.doc["weighing_table_lgm"].length;
		for (var i = 0; i < no_of_ingredients; i++){
			if (ingredients_list[i]["verify"] != 1){
				frappe.throw({
					message: __(`Ingredient ${i+1} weight is not measured yet.`),
					indicator: 'red'
				})
				return false;
			}
		}
	}
});


// // child table 
// frappe.ui.form.on('Ingredients Weighing Table LGM', {
//     // cdt is Child DocType name i.e Quotation Item
//     // cdn is the row name for e.g bbfcb8da6a
    
// })
