/* Step 1: Create sample dataset */
data employees;
	input id name $ age salary department $;
	datalines;
1 John 28 40000 IT
2 Mary 35 55000 HR
3 David 42 65000 Finance
4 Lisa 30 48000 IT
5 James 50 70000 Finance
;
run;

/* Step 2: Create a new variable */
data employees_updated;
	set employees;

	if age >=40 then
		age_group="Senior";
	else
		age_group="Junior";
run;

/* Step 3: Print dataset */
proc print data=employees_updated;
run;

/* Step 4: Summary statistics */
proc means data=employees_updated;
	class age_group;
	var salary;
run;

/* Step 5: Sort data */
proc sort data=employees_updated out=sorted_data;
	by salary descending;
run;

/* Step 6: Print sorted data */
proc print data=sorted_data;
run;
