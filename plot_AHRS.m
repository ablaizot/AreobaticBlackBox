function plot_AHRS(AHR2)
%Plots AHRS data

figure
A = ones(length(AHR2(:,7)),1)*10;
time_normalized = (AHR2(:,2) - min(AHR2(:,2)))/(max(AHR2(:,2)) - min(AHR2(:,2)));

C = ones(length(AHR2(:,7)),1) ./ AHR2(:,2);
geoscatter(AHR2(:,7),AHR2(:,8),20,time_normalized,"filled")
%cbar = colorbar('Ticks',[0,1],'TickLabels',{'Start','End'});
cbar = colorbar();
cbar.TickLabelsMode=  "auto";
% cbar.Ticks = AHR2(:,2);
% cbar.TickLabels = num2cell(AHR2(:,2));
colormap('jet');
cbar.Label.String = "Time (s)";

title("AHRS Position data")

end