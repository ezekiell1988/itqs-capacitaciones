SELECT 
    t.name AS TableName,
    c.name AS ColumnName,
    ty.name AS DataType,
    c.max_length AS MaxLength,
    c.is_nullable AS IsNullable,
    CASE WHEN ic.column_id IS NOT NULL THEN 1 ELSE 0 END AS IsIdentity
FROM sys.tables t
INNER JOIN sys.columns c ON t.object_id = c.object_id
INNER JOIN sys.types ty ON c.user_type_id = ty.user_type_id
LEFT JOIN sys.identity_columns ic ON c.object_id = ic.object_id AND c.column_id = ic.column_id
WHERE t.name IN ('tbQuestion', 'tbQuestionOption', 'tbOption', 'tbExam', 'tbExamQuestion', 'tbQuestionLanguage', 'tbOptionLanguage', 'tbLanguage')
ORDER BY t.name, c.column_id;
