% ================================
% Multi-polymer scatter ONLY (MATLAB)
% Unique polymer -> unique marker style (~50 supported)
% ================================

filePath = "C:\Users\kasif\Documents\Qatar-Environment-and-Energy-Research-Institute-Internship-Work-\Figures Extracted + Matplotlib\Matplotlib\Master_Contains_all_Polymers_for_Matplotlib.xlsx";

T = readtable(filePath, "VariableNamingRule","preserve");

vars = string(T.Properties.VariableNames);
colPoly = vars(contains(lower(vars), "polymer", "IgnoreCase", true));
colX    = vars(contains(lower(vars), "electrical", "IgnoreCase", true) | contains(lower(vars), "conductivity", "IgnoreCase", true));
colY    = vars(contains(lower(vars), "seeback", "IgnoreCase", true) | contains(lower(vars), "seebeck", "IgnoreCase", true));

colPoly = colPoly(1);
colX    = colX(1);
colY    = colY(1);

poly = strip(string(T.(colPoly)));
poly = regexprep(poly, "\s+", " ");
x = T.(colX);
y = T.(colY);

mask = ~ismissing(poly) & ~isnan(x) & ~isnan(y) & x > 0 & y > 0;
poly = poly(mask);
x = x(mask);
y = y(mask);

polymers = unique(poly, "stable");
n = numel(polymers);

fprintf("Unique polymers: %d\n", n);

% ---- Marker components ----
shapes = {'o','s','^','d','v','>','<','p','h','x','+' ,'*'};
fillStyles = [true false];          % filled / hollow
edgeWidths = [0.8 1.8];             % thin / thick

% ---- Generate marker style table ----
styleList = {};
for s = 1:numel(shapes)
    for f = 1:numel(fillStyles)
        for e = 1:numel(edgeWidths)
            styleList(end+1,:) = { ...
                shapes{s}, ...
                fillStyles(f), ...
                edgeWidths(e) ...
            };
        end
    end
end

nStyles = size(styleList,1);

if n > nStyles
    error("Need %d marker styles but only %d available. Add size variants.", n, nStyles);
end

cols = lines(max(n,7));

% ---- Plot ----
figure("Color","w");
hold on;

for i = 1:n
    idx = poly == polymers(i);
    xi = x(idx);
    yi = y(idx);

    mk  = styleList{i,1};
    isFilled = styleList{i,2};
    lw  = styleList{i,3};
    c   = cols(i,:);

    if isFilled
        scatter(xi, yi, 55, ...
            "Marker", mk, ...
            "MarkerFaceColor", c, ...
            "MarkerEdgeColor", "k", ...
            "LineWidth", lw, ...
            "DisplayName", polymers(i));
    else
        scatter(xi, yi, 55, ...
            "Marker", mk, ...
            "MarkerFaceColor", "none", ...
            "MarkerEdgeColor", c, ...
            "LineWidth", lw, ...
            "DisplayName", polymers(i));
    end
end

set(gca, "XScale","log", "YScale","log");
ylim([1e0 3e3])
xlabel("Electrical Conductivity (S cm^{-1})");
ylabel("Seebeck (micro V K^{-1})");
set(gca, "TickDir","in");
box on;

legend("Location","best", "Box","off");
title(" ");
hold off;




% ================================
% FIGURE 2: α^2σ vs Conductivity
% X: Electrical Conductivity (S cm^-1)
% Y: Power Factor α^2σ (W m^-1 K^-2)
% ================================

% ---- Convert Seebeck to V/K and conductivity to S/m ----
S_V = y .* 1e-6;     % µV/K → V/K
sigma_Sm = x .* 100;   % S/cm → S/m

PF = (S_V.^2) .* sigma_Sm; % α^2σ

figure("Color","w");
hold on;
for i = 1:n
    idx = poly == polymers(i);

    xi = sigma_Sm(idx);   % x-axis stays S/cm
    yi = PF(idx);      % y-axis α^2σ

    mk  = styleList{i,1};
    isFilled = styleList{i,2};
    lw  = styleList{i,3};
    c   = cols(i,:);

    if isFilled
        scatter(xi, yi, 55, ...
            "Marker", mk, ...
            "MarkerFaceColor", c, ...
            "MarkerEdgeColor", "k", ...
            "LineWidth", lw, ...
            "DisplayName", polymers(i));
    else
        scatter(xi, yi, 55, ...
            "Marker", mk, ...
            "MarkerFaceColor", "none", ...
            "MarkerEdgeColor", c, ...
            "LineWidth", lw, ...
            "DisplayName", polymers(i));
    end
end

set(gca, "XScale","log", "YScale","log");
xlabel("Electrical Conductivity (S cm^{-1})");
ylabel('$\alpha^2 \sigma\;(\mathrm{W\, m^{-1}\, K^{-2}})$', ...
       "Interpreter","latex");

set(gca, "TickDir","in");
box on;
legend("Location","best", "Box","off");
title(" ");
hold off;
