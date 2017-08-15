from . import unittest
from shapely.algorithms.polylabel import polylabel, Cell
from shapely.geometry import LineString, Point, Polygon
from shapely.geos import TopologicalError


class PolylabelTestCase(unittest.TestCase):
    def test_polylabel(self):
        """
        Finds pole of inaccessibility for a polygon with a tolerance of 10

        """
        polygon = LineString([(0, 0), (50, 200), (100, 100), (20, 50),
                              (-100, -20), (-150, -200)]).buffer(100)
        label = polylabel(polygon, tolerance=10)
        expected = Point(59.35615556364569, 121.8391962974644)
        self.assertTrue(expected.almost_equals(label))

    def test_invalid_polygon(self):
        """
        Makes sure that the polylabel function throws an exception when provided
        an invalid polygon.

        """
        bowtie_polygon = Polygon([(0, 0), (0, 20), (10, 10), (20, 20),
                                  (20, 0), (10, 10), (0, 0)])
        self.assertRaises(TopologicalError, polylabel, bowtie_polygon)

    def test_cell_sorting(self):
        """
        Tests rich comparison operators of Cells for use in the polylabel
        minimum priority queue.

        """
        polygon = Point(0, 0).buffer(100)
        cell1 = Cell(0, 0, 50, polygon)  # closest
        cell2 = Cell(50, 50, 50, polygon)  # furthest
        self.assertLess(cell1, cell2)
        self.assertLessEqual(cell1, cell2)
        self.assertFalse(cell2 <= cell1)
        self.assertEqual(cell1, cell1)
        self.assertFalse(cell1 == cell2)
        self.assertNotEqual(cell1, cell2)
        self.assertFalse(cell1 != cell1)
        self.assertGreater(cell2, cell1)
        self.assertFalse(cell1 > cell2)
        self.assertGreaterEqual(cell2, cell1)
        self.assertFalse(cell1 >= cell2)

    def test_concave_polygon(self):
        """
        Finds pole of inaccessibility for a concave polygon and ensures that
        the point is inside.

        """
        concave_polygon = LineString([(500, 0), (0, 0), (0, 500),
                                      (500, 500)]).buffer(100)
        label = polylabel(concave_polygon)
        self.assertTrue(concave_polygon.contains(label))


def test_suite():
    return unittest.TestLoader().loadTestsFromTestCase(PolylabelTestCase)
