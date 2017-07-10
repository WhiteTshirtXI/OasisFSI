//Wall
c1 = 0.004;
c2 = 0.004;
c3 = 0.004;
c4 = 0.004;
c5 = 0.003;
Point(1) = {0, 0, 0, c1};
Point(4) = {0, 0.02, 0, c1};

//Tip
Point(2) = {0.35, 0, 0, c2};
Point(3) = {0.35, 0.02, 0, c2};
Point(13) = {0.35, 0.01, 0, c5};

Point(7) = {0.0875, 0.02, 0, c3};
Point(11) = {0.0875, 0, 0, c3};

Point(6) = {0.175, 0.02, 0, c4};
Point(10) = {0.175, 0, 0, c4};

Point(8) = {0.262, 0, 0, c5};
Point(12) = {0.262, 0.02, 0, c5};
//+
Line(1) = {1, 11};
//+
Line(2) = {11, 10};
//+
Line(3) = {10, 8};
//+
Line(4) = {8, 2};
//+
Line(5) = {2, 13};
//+
Line(6) = {13, 3};
//+
Line(7) = {3, 12};
//+
Line(8) = {12, 6};
//+
Line(9) = {6, 7};
//+
Line(10) = {7, 4};
//+
Line(11) = {4, 1};
//+
Line Loop(1) = {10, 11, 1, 2, 3, 4, 5, 6, 7, 8, 9};
//+
Plane Surface(1) = {1};
