SELECT 
tr.name, tr.value, tr.timestamp, 
CASE 
    WHEN yi.id_income != -1 THEN (SELECT inc.name FROM incomes AS inc WHERE inc.id=yi.id_income)
    WHEN yi.id_payment != -1 THEN (SELECT payment.name FROM payment_content AS payment WHERE payment.id=yi.id_payment)
END,
CASE
    WHEN pay.id_teller != -1 THEN (SELECT te.name FROM teller AS te WHERE te.id=pay.id_teller)
    WHEN pay.id_payment != -1 THEN (SELECT payment.name FROM payment_content AS payment WHERE payment.id=pay.id_payment)
END
FROM transactions AS tr
INNER JOIN yield AS yi ON yi.id=tr.id_from
INNER JOIN payer AS pay ON pay.id=tr.id_to
WHERE tr.id_user=?
ORDER BY tr.timestamp;