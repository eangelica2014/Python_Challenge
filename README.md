# Python Challenge
## Mummy Money Get Rich&trade;
Dashboard for Mr. Mummy to moniter his income. Once the scheme starts, Mr. Mummy can track his income in real time using the dashboard.

![alt text](https://github.com/vishalbharti1990/Python_Challenge/blob/master/snap.png)

**The dash has the following components:**
* Mummy Money Trend: This component has a dropdown selector and a line graph. Using the dropdown, the money trend for any member can be observed. The figure updates in real time when dropdown selection changes and also updates regular interval of 10 seconds, simulating a weeks trend.
* Stats Card: Shows the stats for current week. It also has the "END SCHEME" button, which ends the MUMMY MONEY scheme and Mr. Mummy can walk away with the earnings.
* New Recruits: Shows the list of new members recruited this week.
* Eliminated: Shows the list of members eliminated from the scheme, as their tenure ran out.
* Withdrawn: Shows the list of members, who left the program deliberately (modeled through a random probability generated from unifrom random distribution and marking the member for withdrawal if this is greator than a threshold(0.85)).
