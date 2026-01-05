% ================================
% Multi-polymer scatter + CURVED best-fit lines (MATLAB)
% X = Electrical Conductivity, Y = Seebeck
% Curved fit: polynomial in log-log space
% ================================

% ---- 1) Path (your file is Excel) ----
filePath = "C:\Users\kasif\Documents\Qatar-Environment-and-Energy-Research-Institute-Internship-Work-\Figures Extracted + Matplotlib\Matplotlib\Master_Contains_all_Polymers_for_Matplotlib.xlsx";

% ---- 2) Read table ----
T = readtable(filePath, "VariableNamingRule","preserve");

% ---- 3) Show actual column names ----
disp("Detected column names:");
disp(T.Properties.VariableNames);

% ---- 4) Find columns by keyword (robust) ----
vars = string(T.Properties.VariableNames);

colPoly = vars(contains(lower(vars), "polymer", "IgnoreCase", true));
colX    = vars(contains(lower(vars), "electrical", "IgnoreCase", true) | contains(lower(vars), "conductivity", "IgnoreCase", true));
colY    = vars(contains(lower(vars), "seeback", "IgnoreCase", true) | contains(lower(vars), "seebeck", "IgnoreCase", true));

colPoly = colPoly(1);
colX    = colX(1);
colY    = colY(1);

fprintf("Using columns:\n Polymer: %s\n X: %s\n Y: %s\n", colPoly, colX, colY);

% ---- 5) Extract and clean ----
poly = string(T.(colPoly));
x = T.(colX);
y = T.(colY);

mask = ~ismissing(poly) & ~isnan(x) & ~isnan(y) & x > 0 & y > 0;
poly = poly(mask);
x = x(mask);
y = y(mask);

polymers = unique(poly, "stable");
n = numel(polymers);

% ---- 6) Styles ----
markers = {'o','s','^','d','v','>','<','p','h','x','+','*'};
cols = lines(max(n, 7));

% ---- 6.1) CURVE SETTINGS ----
deg = 2;                 % try 2 first. If too straight, set deg = 3
nLine = 300;             % smoothness of fitted curve

% ---- 7) Plot ----
figure("Color","w");
hold on;

for i = 1:n
    name = polymers(i);
    idx = poly == name;

    xi = x(idx);
    yi = y(idx);

    % sort by x
    [xi, ord] = sort(xi);
    yi = yi(ord);

    % Optional: if too few points, skip curved fit
    if numel(xi) < (deg + 1)
        degUse = 1;
    else
        degUse = deg;
    end

    mk = markers{mod(i-1, numel(markers)) + 1};
    c  = cols(i, :);

    % scatter points
    scatter(xi, yi, 55, "Marker", mk, "MarkerFaceColor", c, ...
        "MarkerEdgeColor", "none", "MarkerFaceAlpha", 0.9);

    % ---- CURVED log-log polynomial fit ----
    lx = log10(xi);
    ly = log10(yi);

    p = polyfit(lx, ly, degUse);     % polynomial in log space

    xline = logspace(log10(min(xi)), log10(max(xi)), nLine);
    yline = 10.^polyval(p, log10(xline));

    if degUse == 1
        fitTag = sprintf("log-linear (m=%.2f)", p(1));
    else
        fitTag = sprintf("log-poly deg %d", degUse);
    end

    plot(xline, yline, "--", "LineWidth", 0.5, "Color", c, ...
        "DisplayName", sprintf("%s  (%s)", name, fitTag));
end

% ---- 8) Axes formatting ----
set(gca, "XScale","log", "YScale","log");
xlabel("Electrical Conductivity (S m^{-1})");
ylabel("Seebeck (micro V K^{-1})");
set(gca, "TickDir","in");
box on;

legend("Location","best", "Box","off");
title("From Paper -> Charge-transport model for conducting polymers");
hold off;
