# Asset management

## Managed assets

일반 에셋은 제목, 원본 파일명, 유형, 상태, 그룹, 태그, 작성자와 저장 위치를 가집니다. 문서는 에셋을 소유하지 않고 연결하므로 하나의 파일을 여러 문서에서 재사용할 수 있습니다.

## External catalog adapter

어댑터는 외부 검색 응답을 아래 공통 형태로 정규화합니다.

```json
{
  "resource_id": "32-character-resource-id",
  "name": "Asset name",
  "category": "hair",
  "thumbnail_url": "https://images.example.com/item.webp",
  "variants": []
}
```

공개판의 URL은 예시입니다. 실제 연동에서는 `EXTERNAL_CATALOG_SEARCH_URL`과 `EXTERNAL_CATALOG_THUMBNAIL_URL_TEMPLATE`을 허가받은 API에 맞게 설정하고 응답 변환부를 조정합니다.

## Import pipeline

1. 검색어와 페이지 범위를 검증합니다.
2. 외부 응답을 공통 모델로 정규화합니다.
3. 리소스 ID와 콘텐츠 형식을 검증합니다.
4. WebP를 RGBA PNG로 변환합니다.
5. 체크섬과 `(source_provider, source_resource_id)`로 중복을 방지합니다.
6. 파일은 local 또는 R2에 저장하고 메타데이터는 repository에 기록합니다.
7. 선택적으로 변형 그룹을 Avatar Catalog에 UPSERT합니다.

## Demo data

`database/seeds/avatar_asset_variants.csv`는 구조 확인용 가상 데이터만 포함합니다. 실제 제품 데이터나 제3자 자산 식별자는 포함하지 않습니다.

