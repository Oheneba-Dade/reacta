INSERT INTO tag_definitions (label) VALUES
  ('shock'),
  ('joy'),
  ('disgust'),
  ('fear'),
  ('anger'),
  ('surprise'),
  ('laughter'),
  ('confusion'),
  ('excitement')
ON CONFLICT (label) DO NOTHING;
