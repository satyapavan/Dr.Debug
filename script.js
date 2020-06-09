function createTable(domainName, tableName, tableData) {
    var table = document.createElement('table');
    table.classList.add('table');
    table.classList.add('table-striped');
    table.classList.add('table-bordered');
    table.classList.add('table-hover');

    var tableBody = document.createElement('tbody');
    var tableHead = document.createElement('thead');



    var headRow = true;
    tableData.forEach(function(rowData) {
        var row = document.createElement('tr');
        if(headRow) {
            row.classList.add('table-primary');
            
            rowData.forEach(function(cellData) {
                var cell = document.createElement('th');
                cell.appendChild(document.createTextNode(cellData));
                row.appendChild(cell);
            });

            tableHead.appendChild(row);

            headRow = false;
        }
        else {
            rowData.forEach(function(cellData) {
                var cell = document.createElement('td');
                cell.appendChild(document.createTextNode(cellData));
                row.appendChild(cell);
            });
            
            tableBody.appendChild(row);
        }
    });
        
    table.appendChild(tableHead);
    table.appendChild(tableBody);

    var tCard = document.createElement('div');
    tCard.classList.add('card');

    var tCardHead = document.createElement('div');
    tCardHead.classList.add('card-header');
    tCardHead.classList.add('text-white');
    tCardHead.classList.add('bg-secondary');
    tCardHead.classList.add('font-weight-bold');
    tCardHead.innerText = domainName + '.' + tableName;

    var tCardBody = document.createElement('div');
    tCardBody.classList.add('card-body');
    tCardBody.appendChild(table);

    tCard.appendChild(tCardHead);
    tCard.appendChild(tCardBody);

    document.getElementById('master-container').appendChild(tCard);
}

function processResponse(data){
    console.log("Inside processResponse()", data);  
    console.log(data["EMPLOYEE"]); 

    for(key in data) {
        console.log('Domain Name = ' + key);
        for (itrTable in data[key]) {
            
            if( Array.isArray(data[key][itrTable]) ) {
                console.log('Table Name = ' + itrTable + ' :: isArray = ' + Array.isArray(data[key][itrTable]))
                createTable(key, itrTable, data[key][itrTable])
            }
            else {
                console.log('Key = ' + itrTable + ' :: value = ' + data[key][itrTable]);
            }
        }
    }
}

function startTrouble(env, key, value) {
    console.log('Entering into startTrouble');

    async function getData() {
        let response = await fetch('/t-rex/api/query?ENV=' + env + '&KEY=' + key + '&VALUE=' + value);
        let data = await response.json();
        return data;
    }

    getData().then( data => processResponse(data) );
}

document.getElementById("id-submit").addEventListener("click", function(){
    console.log('Entered into submit form');

    var t_env = document.getElementById("id-env").value;
    console.log(t_env)

    var t_key = document.getElementById("id-key").value;
    console.log(t_key)

    var t_value = document.getElementById("id-value").value;
    console.log(t_value)

   
    if( t_value == '' ){
        document.getElementById("id-value").classList.add('is-invalid');
        return;
    }
    else {
        document.getElementById("id-value").classList.remove('is-invalid');
    }

    startTrouble(t_env, t_key, t_value);

} );


//window.addEventListener("DOMContentLoaded", startTrouble, false);