"""Regressions for calendar status: never guess a year or an ambiguous date."""
import unittest
from datetime import date
from experience import event_dates, event_state
from fetch_kinki_hokuriku import parse_calendar


class CalendarDates(unittest.TestCase):
    def test_status_uses_end_of_multi_day_event(self):
        event = {'year':2026,'date_text':'9月10日～13日'}
        self.assertEqual(event_state(event,date(2026,9,9)), '開催予定')
        self.assertEqual(event_state(event,date(2026,9,13)), '開催期間中')
        self.assertEqual(event_state(event,date(2026,9,14)), '終了')

    def test_old_year_stays_past(self):
        self.assertEqual(event_state({'year':2025,'date_text':'9月10日～13日'},date(2026,9,12)), '終了')

    def test_unknown_year_is_not_current(self):
        self.assertIsNone(event_dates({'date_text':'9月10日'}))

    def test_ambiguous_or_invalid_dates_are_not_guessed(self):
        for text in ['12月12日or13日','2月30日','日程未定','9月13日～10日']:
            with self.subTest(text=text):
                self.assertIsNone(event_dates({'year':2026,'date_text':text}))

    def test_year_crossing(self):
        self.assertEqual(event_dates({'year':2026,'date_text':'12月30日～1月2日'}), (date(2026,12,30),date(2027,1,2)))

    def test_source_year_is_preserved(self):
        rows = parse_calendar('<h2>2027年度スケジュール</h2><h3>9月10日～13日</h3><p>学生選手権大会</p>')
        self.assertEqual(rows[0]['year'],2027)

    def test_missing_heading_does_not_guess_source_year(self):
        self.assertIsNone(parse_calendar('<h3>9月10日</h3><p>学生選手権大会</p>')[0]['year'])


if __name__ == '__main__':
    unittest.main()
