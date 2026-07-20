import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const input = await FileBlob.load("data/ofrs_merge.xlsx");
const workbook = await SpreadsheetFile.importXlsx(input);
const overview = await workbook.inspect({
  kind: "region",
  sheetId: "Sheet1",
  range: "A1:AT4",
  maxChars: 12000,
  tableMaxRows: 4,
  tableMaxCols: 46,
  tableMaxCellChars: 240,
});

console.log(overview.ndjson);
