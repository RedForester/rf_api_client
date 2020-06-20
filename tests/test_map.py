import pytest

from rf_api_client import RfApiClient
from rf_api_client.models.nodes_api_models import CreateNodeDto, CreateNodePropertiesDto, PositionType, \
    CreateNodeLinkDto, NodeUpdateDto, PropertiesUpdateDto, GlobalPropertyUpdateDto
from tests.conftest import Secret
from tests.prepare_map import prepare_map


@pytest.mark.asyncio
async def test_login(secret: Secret, api: RfApiClient):
    user = await api.users.get_current()

    assert user.username == secret.username


@pytest.mark.asyncio
async def test_read_maps(api: RfApiClient):
    maps = await api.maps.get_all_maps()

    assert len(maps) >= 0


@pytest.mark.asyncio
async def test_nodes(secret: Secret, api: RfApiClient):
    m = await prepare_map(api, secret.developer_prefix, 'test_create_nodes')

    p = CreateNodePropertiesDto.empty()
    p.global_.title = 'first_node'
    child_1 = await api.nodes.create(CreateNodeDto(
        map_id=m.id,
        parent=m.root_node_id,
        type_id=None,
        position=(PositionType.R, '1'),
        properties=p
    ))

    # link to first_node, also child of first_node
    _ = await api.nodes.create(CreateNodeLinkDto(
        map_id=m.id,
        parent=child_1.id,
        position=(PositionType.R, '1'),
        link=child_1.id
    ))

    # read all nodes
    nodes = await api.maps.get_map_nodes(m.id)

    c1 = nodes.body.children[0]
    c2 = c1.body.children[0]

    # check if c2 is the link to c1
    assert c1.id == c1.body.id
    assert c2.id != c2.body.id
    assert c2.body.id == c1.body.id

    c1_updated = await api.nodes.update_by_id(child_1.id, NodeUpdateDto(
        properties=PropertiesUpdateDto(
            update=[
                GlobalPropertyUpdateDto(
                    key='title',
                    value='first_node_updated'
                )
            ]
        )
    ))

    assert c1_updated.body.properties.global_.title == 'first_node_updated'

    # delete the first node (also delete the second node, which is a link to the first)
    await api.nodes.delete_by_id(child_1.id)

    # read all nodes again and check if both c1 and c2 are deleted
    repeated_nodes = await api.maps.get_map_nodes(m.id)

    assert len(repeated_nodes.body.children) == 0