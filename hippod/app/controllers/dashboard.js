"use strict";

hippoD.controller("DashboardCtrl", function ($scope, ResourcesService) {

  $scope.diskConsumptionData = null;

	ResourcesService.getRessource().then(function(res) {
		var data_array = res['data']['data']['item-bytes-overtime']
		var bytes_actual = data_array[data_array.length - 1][1]
		$scope.overall_data_byte_human = prettyNumber(bytes_actual, 'iec');
		$scope.overall_data_byte_vanilla = bytes_actual;

		var new_array = new Array();
		angular.forEach(data_array, function(value, key) {
			var unix_tm = new Date(value[0]).getTime() / 1000;
			new_array.push([unix_tm, value[1]]);
		});

    $scope.diskConsumptionData = [
			{
				"key": "Series 1",
				"values": new_array
			}
    ];

	}, function(error) {
		$scope.overall_data_byte_human = "unknown (API error)";
		$scope.overall_data_byte_vanilla = "unknown (API error)";
	});

	$scope.yAxisTickFormatFunction = function(){
		return function(d){
      return prettyNumber(d, 'iec');
		}
	}


});
