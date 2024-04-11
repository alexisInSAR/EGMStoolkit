%   EGMStoolkit
%       MATLAB class for EGMStoolkit
%
%       The class allows to import and manipulate the EGMS results in
%       MATLAB.
%
%       Part of EGMStoolkit
%
%   -------------------------------------------------------
%   Authors:    Alexis Hrysiewicz, UCD / iCRAG
%   Version:    0.2.4 Beta
%   Date:       11/04/2024
%
%   -------------------------------------------------------
%   Modified:
%           - None
%
%   -------------------------------------------------------
%   Version history:
%       0.2.7 Beta:     Initial (unreleased)
%
%   -------------------------------------------------------
%   Copyright: 2024 Alexis Hrysiewicz (UCD / iCRAG)
%
%   -------------------------------------------------------
%   -------------------------------------------------------
%   Example:
%       data =
%       EGMStoolkit('EGMS_L3_2018_2022_1_UD_clipped.csv','delimiter',';','verbose',true);
%       % delimiter and verbose options are optional; 
%       data.plot('mean_velocity','geobasemap',true,'ts_plot',true); 
%           % geobasemap will create a map with satellite imagery (optional, True by default). 
%           % ts_plot will will ask the user to create time series plot (optional, False by default). 
%

classdef EGMStoolkit
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    %% Class properties
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    properties (Access = public)
        longitude(:,1) double {mustBeReal, mustBeReal} = [] % Vector of longitude. Default value is []. 
        latitude(:,1) double {mustBeReal, mustBeReal} = [] % Vector of latitude. Default value is []. 
        easting(:,1) double {mustBeReal, mustBeReal} = [] % Vector of easting. Default value is []. 
        northing(:,1) double {mustBeReal, mustBeReal} = [] % Vector of northing. Default value is []. 
        height(:,1) double {mustBeReal, mustBeReal} = [] % Vector of height. Default value is []. 
        height_wgs84(:,1) double {mustBeReal, mustBeReal} = [] % Vector of height_wgs84. Default value is []. 

        line(:,1) double {mustBeReal, mustBeReal} = [] % Vector of line. Default value is []. 
        pixel(:,1) double {mustBeReal, mustBeReal} = [] % Vector of pixel. Default value is []. 

        rmse(:,1) double {mustBeReal, mustBeReal} = [] % Vector of rmse. Default value is []. 

        temporal_coherence(:,1) double {mustBeReal, mustBeReal} = [] % Vector of temporal_coherence. Default value is []. .
        amplitude_dispersion(:,1) double {mustBeReal, mustBeReal} = [] % Vector of amplitude_dispersion. Default value is []. 

        incidence_angle(:,1) double {mustBeReal, mustBeReal} = [] % Vector of incidence_angle. Default value is []. 
        track_angle(:,1) double {mustBeReal, mustBeReal} = [] % Vector of track_angle. Default value is []. 
        los_east(:,1) double {mustBeReal, mustBeReal} = [] % Vector of los_east. Default value is []. 
        los_north(:,1) double {mustBeReal, mustBeReal} = [] % Vector of los_north. Default value is []. 
        los_up(:,1) double {mustBeReal, mustBeReal} = [] % Vector of los_up. Default value is []. 

        mean_velocity(:,1) double {mustBeReal, mustBeReal} = [] % Vector of mean_velocity. Default value is []. 
        mean_velocity_std(:,1) double {mustBeReal, mustBeReal} = [] % Vector of mean_velocity_std. Default value is []. 
        acceleration(:,1) double {mustBeReal, mustBeReal} = [] % Vector of acceleration. Default value is []. 
        acceleration_std(:,1) double {mustBeReal, mustBeReal} = [] % Vector of acceleration_std. Default value is []. 
        seasonality(:,1) double {mustBeReal, mustBeReal} = [] % Vector of seasonality. Default value is []. 
        seasonality_std(:,1) double {mustBeReal, mustBeReal} = [] % Vector of seasonality_std. Default value is []. 

        displacement(:,:) double {mustBeReal, mustBeReal} = [] % Matrix of displacement. Default value is []. 
        time(:,:) datetime {mustBeVector} = NaT(1) % Time vector (in datetime). Default value is NaT. 

        verbose (1,:) logical = true % Verbose mode (can be true or false)
    end

    properties (Access = private)
        filename (1,:) char {mustBeText} = ''
    end

    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    %% Methods
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    methods
        %% Method to read the EGMS file
        function obj = EGMStoolkit(filename,varargin)

            % Create the input parameters
            p = inputParser;

            defaultDelimiter = ';';
            validDelimiters = {';',' ',',','/'};
            checkDelimiter = @(x) any(validatestring(x,validDelimiters));

            addRequired(p,'filename',@ischar);
            addOptional(p,'delimiter',defaultDelimiter,checkDelimiter)
            addOptional(p,'verbose',true,@islogical)

            try
                parse(p,filename,varargin{:});
            catch
                error('A filename is required.')
            end

            obj.verbose = p.Results.verbose;

            if obj.verbose
                fprintf(1,'EGMStoolkit: import EGMS data into MATLAB...\n');
                fprintf(1,'\tFilename: %s\n',p.Results.filename);
                fprintf(1,'\tDelimiter: %s\n',p.Results.delimiter);
            end

            if exist(p.Results.filename)==0
                error('The file does not exist.')
            else
                obj.filename = p.Results.filename;
            end

            % Read the header
            fid = fopen(obj.filename,'rt'); headerline = fgetl(fid); fclose(fid);
            headerline = strsplit(headerline,p.Results.delimiter);

            % Read the data
            data = readtable(obj.filename,'Headerlines',1);

            % Reorgnaise the dataset
            time = [];
            displacement = [];

            for idx = 1 : length(headerline)

                if (strcmp(headerline{idx},'pid') == 0) & (strcmp(headerline{idx},'mp_type') == 0)

                    if isempty(strfind(headerline{idx},'2')) == 0
                        displacement = [displacement table2array(data(:,idx))];
                        time = [time; datetime(headerline{idx},'InputFormat','uuuuMMdd')];
                    else
                        eval(sprintf('obj.%s=table2array(data(:,idx));',headerline{idx}))
                    end
                    
                end
            end

            obj.displacement = displacement;
            obj.time = time;

            % Re-projection
            if isempty(obj.latitude) || all(isnan(obj.latitude))
                proj = projcrs(3035,'Authority','EPSG');
                [obj.latitude,obj.longitude] = projinv(proj,obj.easting,obj.northing);
            end

            if obj.verbose
                fprintf(1,'done.\n')
            end

        end

        %% The method will display a map
        function plot(obj,varargin)
            
            % Create the input parameters
            p = inputParser;
            addOptional(p,'parameter','mean_velocity',@ischar)
            addOptional(p,'geobasemap',true,@islogical)
            addOptional(p,'ts_plot',false,@islogical)
            parse(p,varargin{:});

            % Check the dataset
            if ischar(p.Results.parameter)
                try
                    eval(sprintf('tmp = obj.%s;',p.Results.parameter));
                catch
                    error('The parameter is not in the dataset.');
                end
            else
                error('The parameter should be a string.');
            end

            if isempty(tmp) || all(isnan(tmp))
                error('No data for this parameter.');
            end

            % Plot the map
            fig1 = figure('Name',sprintf('%s from %s',replace(p.Results.parameter,'_',' '),obj.filename),'NumberTitle','on');
            if p.Results.geobasemap
                geoscatter(obj.latitude,obj.longitude,[],tmp,'filled'); colormap jet; c1 = colorbar; ylabel(c1,p.Results.parameter); caxis([quantile(tmp,0.1) quantile(tmp,0.9)]);
                geobasemap('satellite');
                title(sprintf('%s',replace(p.Results.parameter,'_',' ')));
            else
                scatter(obj.longitude,obj.latitude,[],tmp,'filled'); colormap jet; c1 = colorbar; ylabel(c1,p.Results.parameter); caxis([quantile(tmp,0.1) quantile(tmp,0.9)]);
                ylabel('Latitude');
                xlabel('Longitude');
                title(sprintf('%s',replace(p.Results.parameter,'_',' ')));
            end

            % Time series plot (with interaction)
            if p.Results.ts_plot == true
                if ((isempty(tmp) == 0) || (all(isnan(tmp)) == 0))

                    user_check = true;
                    dt = delaunayTriangulation(obj.longitude,obj.latitude);
                    while user_check
                        figure(fig1);

                        if p.Results.geobasemap
                            [y,x] = ginput(1);
                        else
                            [x,y] = ginput(1);
                        end

                        idx = nearestNeighbor(dt,x,y);

                        if obj.verbose
                            fprintf('Plot the time series of displacements for point %d (%f / %f)\n',idx,obj.latitude(idx),obj.longitude(idx));
                            try
                                fprintf('\tVelocity of %f (STD: %f) [mm/yr]\n',obj.mean_velocity(idx),obj.mean_velocity_std(idx));
                            catch
                                a = 'dummy'; 
                            end 
                        end

                        figi = figure('Name',sprintf('Time series for %s',obj.filename),'NumberTitle','on');

                        plot(obj.time,obj.displacement(idx,:),'*k'); 
                        ymod = polyval(polyfit(datenum(obj.time),obj.displacement(idx,:)',1),datenum(obj.time)); 
                        hold on; plot(obj.time,ymod,'--b'); hold off; 
                        xlabel('Time'); 
                        ylabel('Displacements [mm]'); 
                        grid on; grid minor; 
                        lg = legend('Time series','Linear trend'); 
                        title(sprintf('Point %d (%f / %f)',idx,obj.latitude(idx),obj.longitude(idx))); 

                        user_answer = input('Do you want to continue ? [y] ');
                        if isempty(user_answer)
                            user_check = true; 
                        else
                            user_check = false; 
                        end 
                    end
                else
                    error('The displacement time series is not available in this dataset.');
                end
            end
        end
    end 
end 


