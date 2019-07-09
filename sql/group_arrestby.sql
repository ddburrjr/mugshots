SELECT arrest_by AS 'Arrested By', COUNT(*) AS Total
FROM mugshots.inmates
GROUP BY arrest_by
ORDER BY COUNT(*) DESC